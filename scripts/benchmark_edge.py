import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import json,time,platform
from pathlib import Path
import numpy as np
import tensorflow as tf
root=Path(__file__).resolve().parents[1]
metadata=json.loads((root/'edge/models/metadata.json').read_text())
model=tf.lite.Interpreter(model_path=str(root/'edge/models/edgeguard_int8.tflite'),num_threads=1)
model.allocate_tensors();inp=model.get_input_details()[0]
model.set_tensor(inp['index'],np.zeros((1,36),dtype=np.int8))
for _ in range(20):model.invoke()
measurements=[]
for _ in range(1000):
    t=time.perf_counter_ns();model.invoke();measurements.append((time.perf_counter_ns()-t)/1e6)
result={'measurement_target':'HOST CPU ONLY','host':platform.platform(),'samples':1000,'p50_ms':float(np.quantile(measurements,.5)),'p95_ms':float(np.quantile(measurements,.95)),'model_size_bytes':(root/'edge/models/edgeguard_int8.tflite').stat().st_size,'mcu_latency_ms':None,'tensor_arena_bytes':None,'peak_ram_bytes':None}
(root/'edge/models/host_benchmark.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
