#include "../firmware/edgeguard.hpp"
#include <cassert>
#include <iostream>
int main(){
 skyguard::RingBuffer<skyguard::Sample,3> buffer;
 for(uint32_t i=0;i<5;++i)buffer.push({i*60000ULL,i,25,1000,60});
 assert(buffer.size()==3 && buffer.dropped()==2 && buffer.front()->sequence==2);
 buffer.acknowledge();assert(buffer.front()->sequence==3);
 skyguard::Guard guard;
 auto a=guard.screen({1000,1,25,1000,60});assert(a.state==skyguard::EdgeState::Normal);
 auto b=guard.screen({61000,2,42,1000,60});assert(b.state==skyguard::EdgeState::Critical);
 auto c=guard.screen({61000,3,42,1000,60});assert(c.timing_error);
 auto d=guard.screen({121000,4,42,1000,130});assert(d.state==skyguard::EdgeState::Critical);
 auto e=guard.screen({3661000,5,42,1000,60});assert(e.frozen);
 std::cout<<"Edge rules, timestamp checks, FIFO replay and overflow accounting passed.\n";
}
