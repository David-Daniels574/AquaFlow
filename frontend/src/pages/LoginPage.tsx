import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary/20 to-background p-4 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-[url('/savewater.jpg')] bg-cover bg-center opacity-5"></div>
      
      {/* Floating Water Droplets */}
      <div className="absolute top-20 left-20 w-4 h-4 bg-primary/30 rounded-full animate-bounce"></div>
      <div className="absolute top-40 right-32 w-6 h-6 bg-primary/20 rounded-full animate-bounce" style={{animationDelay: '1s'}}></div>
      <div className="absolute bottom-32 left-32 w-5 h-5 bg-primary/25 rounded-full animate-bounce" style={{animationDelay: '2s'}}></div>
      <div className="absolute bottom-20 right-20 w-3 h-3 bg-primary/35 rounded-full animate-bounce" style={{animationDelay: '0.5s'}}></div>
      
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <span className="text-2xl">💧</span>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-primary mb-2">AquaFlow</h1>
          <p className="text-muted-foreground">Smart Water Management Platform</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}