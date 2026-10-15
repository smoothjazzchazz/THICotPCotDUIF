// Training-only multiclass focal loss, gamma=2; forward state/logits are unchanged.
// Sparse scalar CPU kernel. Python owns data, masks, checkpoints and orchestration.
// All arithmetic is double; no fast-math or parallel reduction is used.
#include <cmath>
#include <vector>
#include <algorithm>
#include <cstdint>

extern "C" void fixed_sequence(int T,int N,int E,const int* src,const int* dst,
 const int* delay,const double* alpha,const double* p,const double* x,
 double* h,double* logits,const int* activation) {
 const int P=E+7*N+6,O=E+N,B=E+7*N;
 std::vector<int64_t> weights(P),old(N),now(N),leak(N);
 for(int i=0;i<P;i++) weights[i]=std::llround(p[i]*4096);
 for(int i=0;i<N;i++) {old[i]=std::llround(h[i]*4096);leak[i]=std::llround(alpha[i]*4096);}
 std::vector<int> begin(N+1,0);
 for(int e=0;e<E;e++) begin[dst[e]+1]++;
 for(int i=1;i<=N;i++) begin[i]+=begin[i-1];
 auto rounded=[](int64_t v,int64_t d){return v>=0?(v+d/2)/d:-((-v+d/2)/d);};
 for(int t=0;t<T;t++) {
  for(int i=0;i<N;i++) {
   int64_t z=weights[E+i]*4096;
   for(int e=begin[i];e<begin[i+1];e++) {
    int64_t v=src[e]<0?std::llround(x[t*9-1-src[e]]*4096):(delay[e]?old[src[e]]:now[src[e]]);
    z+=weights[e]*v;
   }
   // Q24 accumulator to nearest LUT address; tanh table has 1/256 input steps.
   int64_t address=std::max<int64_t>(0,std::min<int64_t>(4096,rounded(z,65536)+2048));
   now[i]=rounded((4096-leak[i])*old[i]+leak[i]*activation[address],4096);
   now[i]=std::max<int64_t>(-32768,std::min<int64_t>(32767,now[i]));
  }
  for(int k=0;k<6;k++) {
   int64_t z=weights[B+k]*4096;
   for(int i=0;i<N;i++) z+=weights[O+k*N+i]*now[i];
   logits[t*6+k]=double(z)/16777216.;
  }
  old.swap(now);
 }
 for(int i=0;i<N;i++) h[i]=double(old[i])/4096.;
}

extern "C" double sequence(int T,int N,int E,const int* src,const int* dst,
 const int* delay,const double* alpha,const double* p,const double* x,
 const int* y,const double* cw,double* h,double* logits,double* grad,
 double* initial_gradient,int backward,int readout_only,int quantize) {
 const int P=E+7*N+6, O=E+N, B=E+7*N;
 std::vector<double> states((T+1)*N), proposal(T*N), adj((T+1)*N,0.);
 std::copy(h,h+N,states.begin());
 std::vector<int> begin(N+1,0);
 for(int e=0;e<E;e++) begin[dst[e]+1]++;
 for(int i=1;i<=N;i++) begin[i]+=begin[i-1];
 if(backward) std::fill(grad,grad+P,0.);
 double loss=0.;
 for(int t=0;t<T;t++) {
  double* now=&states[(t+1)*N]; const double* old=&states[t*N];
  for(int i=0;i<N;i++) {
   double z=p[E+i];
   for(int e=begin[i];e<begin[i+1];e++) {
    double v=src[e]<0?x[t*9-1-src[e]]:states[(t+1-delay[e])*N+src[e]];
    z+=p[e]*v;
   }
   double a=std::tanh(z); proposal[t*N+i]=a;
   now[i]=(1-alpha[i])*old[i]+alpha[i]*a;
   if(quantize) now[i]=std::round(now[i]*4096)/4096;
  }
  double top=-1e300, prob[6], sum=0.;
  for(int k=0;k<6;k++) {
   double z=p[B+k]; for(int i=0;i<N;i++) z+=p[O+k*N+i]*now[i];
   logits[t*6+k]=z; top=std::max(top,z);
  }
  for(int k=0;k<6;k++) {prob[k]=std::exp(logits[t*6+k]-top);sum+=prob[k];}
  if(y) {
   double ce=std::max(0.,std::log(sum)+top-logits[t*6+y[t]]);
   double pt=prob[y[t]]/sum, remainder=1-pt;
   double focus=remainder*remainder+2*pt*remainder*ce;
   loss+=cw[y[t]]*remainder*remainder*ce/T;
   if(backward) for(int k=0;k<6;k++) {
    double dz=(prob[k]/sum-(k==y[t]))*cw[y[t]]*focus/T;
    grad[B+k]+=dz;
    for(int i=0;i<N;i++) {grad[O+k*N+i]+=dz*now[i];adj[(t+1)*N+i]+=dz*p[O+k*N+i];}
   }
  }
 }
 if(backward && !readout_only) for(int t=T-1;t>=0;t--) {
  for(int i=N-1;i>=0;i--) {
   double dh=adj[(t+1)*N+i], a=proposal[t*N+i];
   double dz=dh*alpha[i]*(1-a*a);grad[E+i]+=dz;
   adj[t*N+i]+=dh*(1-alpha[i]);
   for(int e=begin[i];e<begin[i+1];e++) {
    int s=src[e], index=(t+1-delay[e])*N+s;
    double v=s<0?x[t*9-1-s]:states[index];grad[e]+=dz*v;
    if(s>=0) adj[index]+=dz*p[e];
   }
  }
 }
 std::copy(states.begin()+T*N,states.end(),h);
 if(initial_gradient) std::copy(adj.begin(),adj.begin()+N,initial_gradient);
 return loss;
}
