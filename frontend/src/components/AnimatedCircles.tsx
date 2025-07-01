
export default function AnimatedCircles() {
  return (
    <>
      <div className="absolute top-20 left-20 w-32 h-32 bg-orange-200 rounded-full opacity-60 animate-bounce-slow"></div>
      <div className="absolute top-40 right-32 w-24 h-24 bg-orange-300 rounded-full opacity-40 animate-float"></div>
      <div className="absolute bottom-32 left-1/4 w-20 h-20 bg-orange-200 rounded-full opacity-50 animate-bounce-slow delay-1000"></div>
      <div className="absolute bottom-20 right-20 w-28 h-28 bg-orange-300 rounded-full opacity-30 animate-float delay-2000"></div>
      <div className="absolute top-1/2 left-10 w-16 h-16 bg-orange-200 rounded-full opacity-40 animate-bounce-slow delay-500"></div>
      <div className="absolute top-10 right-10 w-12 h-12 bg-orange-400 rounded-full opacity-60 animate-float delay-1500"></div>
      <div className="absolute bottom-1/3 right-1/3 w-36 h-36 bg-orange-100 rounded-full opacity-30 animate-bounce-slow delay-3000"></div>
      
      <div className="absolute top-1/4 left-1/2 w-1 h-20 bg-orange-400 opacity-60"></div>
      <div className="absolute bottom-1/4 right-1/4 w-1 h-16 bg-orange-400 opacity-40"></div>
    </>
  )
}
