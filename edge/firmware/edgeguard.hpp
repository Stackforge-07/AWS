#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <cstddef>
#include <algorithm>

namespace skyguard {
enum class EdgeState { Normal, Suspicious, Critical };
struct Sample { uint64_t timestamp_ms; uint32_t sequence; float temperature, pressure, humidity; };
struct Screening { EdgeState state; std::array<float,3> rate_per_minute; bool timing_error; bool frozen; float ewma_residual; };

template <typename T, size_t Capacity> class RingBuffer {
 public:
  static_assert(Capacity > 0);
  void push(const T& value) { if (count_==Capacity) { head_=(head_+1)%Capacity; --count_; ++dropped_; } data_[(head_+count_)%Capacity]=value; ++count_; }
  const T* front() const { return count_?&data_[head_]:nullptr; }
  // Call only after transport acknowledgement. Repeated delivery uses stable observation ID.
  bool acknowledge() { if(!count_)return false; head_=(head_+1)%Capacity;--count_;return true; }
  size_t size() const{return count_;} size_t dropped() const{return dropped_;}
 private: std::array<T,Capacity> data_{}; size_t head_=0,count_=0,dropped_=0;
};
class Guard {
 public:
  Screening screen(const Sample& s) {
   const std::array<float,3> x{s.temperature,s.pressure,s.humidity};
   Screening result{EdgeState::Normal,{0,0,0},false,false,0};
   bool invalid=!std::isfinite(s.temperature)||!std::isfinite(s.pressure)||!std::isfinite(s.humidity)||s.humidity<0||s.humidity>100||s.pressure<100||s.pressure>1200||s.temperature<-90||s.temperature>65;
   if(invalid){result.state=EdgeState::Critical;return result;}
   if(initialized_ && s.timestamp_ms<=previous_.timestamp_ms) {result.state=EdgeState::Suspicious;result.timing_error=true;return result;}
   if(initialized_){
    const float minutes=(s.timestamp_ms-previous_.timestamp_ms)/60000.0f;
    const std::array<float,3> prev{previous_.temperature,previous_.pressure,previous_.humidity};
    constexpr std::array<float,3> scales{0.5f,0.3f,2.0f};
    for(size_t i=0;i<3;++i){
     result.rate_per_minute[i]=(x[i]-prev[i])/minutes;
     if(std::fabs(result.rate_per_minute[i])>scales[i])result.state=EdgeState::Suspicious;
     if(std::fabs(result.rate_per_minute[i])>scales[i]*4)result.state=EdgeState::Critical;
     if(x[i]!=prev[i])last_change_[i]=s.timestamp_ms;
     if(s.timestamp_ms-last_change_[i]>=3600000){result.frozen=true;if(result.state!=EdgeState::Critical)result.state=EdgeState::Suspicious;}
     result.ewma_residual=std::max(result.ewma_residual,std::fabs(x[i]-ewma_[i])/scales[i]);
     ewma_[i]=.2f*x[i]+.8f*ewma_[i];
    }
    if(s.sequence>previous_.sequence+1)result.timing_error=true;
   }else{ewma_=x;last_change_.fill(s.timestamp_ms);initialized_=true;}
   previous_=s;return result;
  }
 private: bool initialized_=false;Sample previous_{};std::array<float,3> ewma_{};std::array<uint64_t,3> last_change_{};
};
}
