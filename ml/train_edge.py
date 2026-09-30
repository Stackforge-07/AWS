"""Train normal-window AE and export fully INT8 TFLite + C bytes. Host measurements only."""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
os.environ['TF_NUM_INTRAOP_THREADS']='2'
os.environ['TF_NUM_INTEROP_THREADS']='2'
import json, time, hashlib, platform
from pathlib import Path
import numpy as np
import tensorflow as tf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'edge/models';OUT.mkdir(parents=True,exist_ok=True)
tf.keras.utils.set_random_seed(26073)
tf.config.experimental.enable_op_determinism()
dataset=np.load(ROOT/'ml/artifacts/edge_training.npz')
train=dataset['train'].astype(np.float32);validation=dataset['validation'].astype(np.float32)
mean=train.mean(axis=0);std=np.maximum(train.std(axis=0),1e-4)
x=(train-mean)/std;val=(validation-mean)/std
model=tf.keras.Sequential([tf.keras.layers.Input(shape=(36,),batch_size=1),tf.keras.layers.Dense(32,activation='relu'),tf.keras.layers.Dense(8,activation='relu'),tf.keras.layers.Dense(32,activation='relu'),tf.keras.layers.Dense(36)])
model.compile(optimizer=tf.keras.optimizers.Adam(.001),loss='mse')
# Explicit batches avoid tf.data background thread pools and keep seed ordering reproducible.
loss=[]
for epoch in range(18):
    for offset in range(0,len(x),64):model.train_on_batch(x[offset:offset+64],x[offset:offset+64])
    error=float(np.mean((model(val,training=False).numpy()-val)**2));loss.append(error)
    print(f'epoch {epoch+1}: validation MSE {error:.6f}',flush=True)
model.save(OUT/'autoencoder.keras')
converter=tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations=[tf.lite.Optimize.DEFAULT]
converter.representative_dataset=lambda:([row[None,:]] for row in x[::max(1,len(x)//300)])
converter.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type=tf.int8;converter.inference_output_type=tf.int8
binary=converter.convert();(OUT/'edgeguard_int8.tflite').write_bytes(binary)
interpreter=tf.lite.Interpreter(model_content=binary,num_threads=1);interpreter.allocate_tensors()
a=interpreter.get_input_details()[0];b=interpreter.get_output_details()[0]
assert a['dtype']==np.int8 and b['dtype']==np.int8
inscale,inzero=a['quantization'];outscale,outzero=b['quantization']
errors=[];latencies=[]
for row in val:
    quant=np.clip(np.rint(row/inscale+inzero),-128,127).astype(np.int8)[None,:]
    interpreter.set_tensor(a['index'],quant)
    start=time.perf_counter_ns();interpreter.invoke();latencies.append((time.perf_counter_ns()-start)/1e6)
    predicted=(interpreter.get_tensor(b['index']).astype(np.float32)-outzero)*outscale
    errors.append(float(np.mean((row-predicted[0])**2)))
threshold=float(np.quantile(errors,.995))
metadata={'model_version':'edgeguard-int8-synthetic-1','seed':26073,'inputs':'12 timestamps × T/P/RH, oldest first','input_dimension':36,'architecture':[36,32,8,32,36],
          'training_rows':len(x),'validation_rows':len(val),'mean':mean.tolist(),'std':std.tolist(),'normal_threshold':threshold,'threshold_method':'99.5th percentile of INT8 validation normal reconstruction MSE',
          'input_quantization':{'scale':inscale,'zero_point':inzero},'output_quantization':{'scale':outscale,'zero_point':outzero},'model_size_bytes':len(binary),
          'host_inference_ms':{'p50':float(np.quantile(latencies,.5)),'p95':float(np.quantile(latencies,.95))},'host':platform.platform(),
          'tensorflow_version':tf.__version__,'physical_hardware_validated':False,'tensor_arena_bytes':None,'peak_ram_bytes':None,'mcu_latency_ms':None,'power_mw':None,
          'sha256':hashlib.sha256(binary).hexdigest(),'validation_history':loss,'source':'synthetic normal windows only; not field validated'}
(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2))
header='#pragma once\n#include <cstdint>\n#include <cstddef>\nnamespace skyguard {\nalignas(16) const unsigned char kModel[] = {\n'
header+='\n'.join(','.join(str(b) for b in binary[i:i+20])+',' for i in range(0,len(binary),20))+'\n};\n'
header+=f'constexpr size_t kModelSize = {len(binary)};\nconstexpr float kThreshold = {threshold:.9f}f;\n'
header+='const float kMean[36] = {'+','.join(f'{v:.8f}f' for v in mean)+'};\n'
header+='const float kStd[36] = {'+','.join(f'{v:.8f}f' for v in std)+'};\n}\n'
(OUT/'model_data.h').write_text(header)
print(json.dumps({k:metadata[k] for k in ('model_size_bytes','normal_threshold','host_inference_ms','physical_hardware_validated')},indent=2))
