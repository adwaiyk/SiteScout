import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Globe2 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
      <div className="flex items-center justify-center h-16 w-16 rounded-full bg-primary/10 mb-8">
        <Globe2 className="h-8 w-8 text-primary" />
      </div>
      
      <h1 className="text-5xl font-extrabold tracking-tight text-slate-900 sm:text-6xl mb-6">
        Deploy Renewables <br />
        <span className="text-primary">With Confidence.</span>
      </h1>
      
      <p className="text-xl text-slate-600 max-w-2xl mb-10">
        SiteScout uses multi-objective optimization and spatial AI to help planners discover, evaluate, and select the optimal locations for solar and wind infrastructure.
      </p>
      
      <div className="flex gap-4">
        <Button asChild size="lg" className="h-12 px-8">
          <Link href="/signup">
            Get Started <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="h-12 px-8">
          <Link href="/login">
            Login
          </Link>
        </Button>
      </div>
    </div>
  );
}