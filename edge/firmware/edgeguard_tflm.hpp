#pragma once
// Integrate with an installed TensorFlow Lite Micro SDK. This adapter is not a flashed board claim.
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "../models/model_data.h"
#include <algorithm>
#include <cmath>
#include <new>

namespace skyguard {
class TinyModel {
 public:
  // Caller supplies and measures arena on target. No fabricated RAM/latency constants.
  TinyModel(uint8_t* arena,size_t arena_size):arena_(arena),arena_size_(arena_size){}
  bool initialize(){
    model_=tflite::GetModel(kModel);
    if(model_->version()!=TFLITE_SCHEMA_VERSION)return false;
    resolver_.AddFullyConnected();resolver_.AddRelu();resolver_.AddReshape();
    interpreter_=new (storage_) tflite::MicroInterpreter(model_,resolver_,arena_,arena_size_);
    if(interpreter_->AllocateTensors()!=kTfLiteOk)return false;
    return interpreter_->input(0)->type==kTfLiteInt8&&interpreter_->output(0)->type==kTfLiteInt8;
  }
  bool score(const float window[36],float& mse){
    if(!interpreter_)return false;
    auto* input=interpreter_->input(0);auto* output=interpreter_->output(0);
    float normalized[36];
    for(int i=0;i<36;++i){normalized[i]=(window[i]-kMean[i])/kStd[i];const int q=std::lround(normalized[i]/input->params.scale)+input->params.zero_point;input->data.int8[i]=static_cast<int8_t>(std::max(-128,std::min(127,q)));}
    if(interpreter_->Invoke()!=kTfLiteOk)return false;
    mse=0;
    for(int i=0;i<36;++i){float y=(output->data.int8[i]-output->params.zero_point)*output->params.scale;float d=y-normalized[i];mse+=d*d;}
    mse/=36;return true;
  }
 private:
  uint8_t* arena_;size_t arena_size_;const tflite::Model* model_=nullptr;
  tflite::MicroMutableOpResolver<3> resolver_;
  alignas(tflite::MicroInterpreter) unsigned char storage_[sizeof(tflite::MicroInterpreter)];
  tflite::MicroInterpreter* interpreter_=nullptr;
};
}
