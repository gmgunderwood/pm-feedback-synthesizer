import { useState } from "react";
import { useAnalyzeFeedback } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { BrainCircuit, CheckCircle2, ChevronRight, AlertCircle, TrendingUp, XCircle, Loader2 } from "lucide-react";

export default function Home() {
  const [feedback, setFeedback] = useState("");
  const [productContext, setProductContext] = useState("");
  
  const mutation = useAnalyzeFeedback();

  const handleAnalyze = () => {
    if (!feedback.trim()) return;
    mutation.mutate({ data: { feedback, productContext: productContext || undefined } });
  };

  const handleClear = () => {
    setFeedback("");
    setProductContext("");
    mutation.reset();
  };

  return (
    <div className="min-h-[100dvh] w-full bg-slate-50 flex justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="w-full max-w-5xl space-y-8">
        
        {/* Header */}
        <header className="space-y-2">
          <div className="flex items-center gap-3 text-primary">
            <BrainCircuit className="w-8 h-8" />
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900" data-testid="text-header">
              Feedback Synthesizer
            </h1>
          </div>
          <p className="text-slate-500 max-w-2xl text-lg">
            Paste raw user feedback to extract actionable insights, themes, and sentiment automatically.
          </p>
        </header>

        {/* Input Section */}
        <Card className="border-slate-200 shadow-sm" data-testid="card-input">
          <CardContent className="pt-6 space-y-6">
            <div className="space-y-2">
              <label htmlFor="product-context" className="text-sm font-medium text-slate-700">
                Product Context <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <Input
                id="product-context"
                placeholder="e.g. B2B SaaS project management tool"
                value={productContext}
                onChange={(e) => setProductContext(e.target.value)}
                className="bg-white"
                data-testid="input-product-context"
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="feedback-input" className="text-sm font-medium text-slate-700">
                Raw Feedback Data
              </label>
              <Textarea
                id="feedback-input"
                placeholder="Paste user interviews, App Store reviews, support tickets, or NPS comments here..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="min-h-[240px] resize-y bg-white text-base"
                data-testid="textarea-feedback"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-slate-500">
                {feedback.length} characters
              </p>
              <div className="flex gap-3">
                {mutation.data && (
                  <Button variant="outline" onClick={handleClear} data-testid="button-clear">
                    Clear
                  </Button>
                )}
                <Button 
                  onClick={handleAnalyze} 
                  disabled={!feedback.trim() || mutation.isPending}
                  className="min-w-[160px]"
                  data-testid="button-analyze"
                >
                  {mutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Data...
                    </>
                  ) : (
                    "Analyze Feedback"
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {mutation.isPending && (
          <div className="py-16 flex flex-col items-center justify-center space-y-6 text-slate-500 animate-in fade-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse"></div>
              <BrainCircuit className="w-16 h-16 text-primary animate-pulse relative z-10" />
            </div>
            <div className="space-y-2 text-center">
              <h3 className="text-lg font-medium text-slate-800">Synthesizing intelligence...</h3>
              <p className="text-sm">Extracting themes, sentiment, and actionable insights.</p>
            </div>
          </div>
        )}

        {/* Results Section */}
        {mutation.data && (
          <div className="space-y-8 animate-in slide-in-from-bottom-4 fade-in duration-700" data-testid="section-results">
            
            {/* Executive Summary */}
            <Card className="border-slate-200 bg-white shadow-sm overflow-hidden" data-testid="card-executive-summary">
              <div className="bg-slate-50 border-b border-slate-100 px-6 py-4 flex items-center justify-between">
                <h2 className="font-semibold text-slate-800">Executive Summary</h2>
                <Badge variant={mutation.data.summary.overallSentiment === "positive" ? "default" : mutation.data.summary.overallSentiment === "negative" ? "destructive" : "secondary"}>
                  {mutation.data.summary.overallSentiment.charAt(0).toUpperCase() + mutation.data.summary.overallSentiment.slice(1)}
                </Badge>
              </div>
              <CardContent className="p-6 space-y-8">
                <p className="text-slate-700 leading-relaxed text-lg" data-testid="text-executive-summary">
                  {mutation.data.summary.executiveSummary}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm font-medium">
                      <span className="text-slate-500">Sentiment Score</span>
                      <span className={mutation.data.summary.sentimentScore > 0 ? "text-green-600" : mutation.data.summary.sentimentScore < 0 ? "text-red-600" : "text-slate-600"}>
                        {mutation.data.summary.sentimentScore.toFixed(2)}
                      </span>
                    </div>
                    <Progress 
                      value={((mutation.data.summary.sentimentScore + 1) / 2) * 100} 
                      className="h-2"
                    />
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Negative (-1)</span>
                      <span>Positive (1)</span>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 flex flex-col justify-center">
                    <span className="text-sm font-medium text-slate-500">Total Themes</span>
                    <span className="text-3xl font-semibold text-slate-800" data-testid="text-total-themes">{mutation.data.summary.totalThemes}</span>
                  </div>

                  <div className="bg-red-50 rounded-lg p-4 border border-red-100 flex flex-col justify-center">
                    <span className="text-sm font-medium text-red-600">Critical Issues</span>
                    <span className="text-3xl font-semibold text-red-700" data-testid="text-critical-issues">{mutation.data.summary.criticalIssues}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Key Insights */}
              <div className="lg:col-span-1 space-y-6">
                <Card className="border-slate-200 shadow-sm h-full" data-testid="card-insights">
                  <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
                    <CardTitle className="text-lg">Key Insights</CardTitle>
                  </CardHeader>
                  <CardContent className="p-6 space-y-8">
                    
                    {mutation.data.summary.keyStrengths.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="flex items-center text-sm font-semibold text-green-700 uppercase tracking-wider">
                          <TrendingUp className="w-4 h-4 mr-2" /> Strengths
                        </h4>
                        <ul className="space-y-2">
                          {mutation.data.summary.keyStrengths.map((strength, idx) => (
                            <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {mutation.data.summary.keyWeaknesses.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="flex items-center text-sm font-semibold text-red-700 uppercase tracking-wider">
                          <AlertCircle className="w-4 h-4 mr-2" /> Weaknesses
                        </h4>
                        <ul className="space-y-2">
                          {mutation.data.summary.keyWeaknesses.map((weakness, idx) => (
                            <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                              <XCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                              <span>{weakness}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {mutation.data.summary.recommendedActions.length > 0 && (
                      <div className="space-y-3 pt-4 border-t border-slate-100">
                        <h4 className="text-sm font-semibold text-indigo-700 uppercase tracking-wider">
                          Recommended Actions
                        </h4>
                        <ul className="space-y-3">
                          {mutation.data.summary.recommendedActions.map((action, idx) => (
                            <li key={idx} className="text-sm text-slate-800 bg-indigo-50/50 p-3 rounded-md border border-indigo-100/50">
                              {action}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  </CardContent>
                </Card>
              </div>

              {/* Themes */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                  Feedback Themes 
                  <Badge variant="secondary" className="font-normal text-xs">{mutation.data.themes.length}</Badge>
                </h3>
                
                <div className="space-y-4">
                  {mutation.data.themes.map((theme, idx) => (
                    <Card key={idx} className="border-slate-200 shadow-sm overflow-hidden" data-testid={`card-theme-${idx}`}>
                      <div className="p-5">
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
                          <div className="space-y-1">
                            <h4 className="text-lg font-medium text-slate-900">{theme.name}</h4>
                            <p className="text-sm text-slate-500">{theme.description}</p>
                          </div>
                          <div className="flex flex-wrap gap-2 shrink-0">
                            <Badge variant="outline" className="bg-slate-50">
                              {theme.occurrences} mentions
                            </Badge>
                            
                            {theme.sentiment === "positive" && <Badge className="bg-green-100 text-green-800 hover:bg-green-100 border-transparent">Positive</Badge>}
                            {theme.sentiment === "negative" && <Badge className="bg-red-100 text-red-800 hover:bg-red-100 border-transparent">Negative</Badge>}
                            {theme.sentiment === "neutral" && <Badge className="bg-slate-100 text-slate-800 hover:bg-slate-100 border-transparent">Neutral</Badge>}
                            {theme.sentiment === "mixed" && <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-transparent">Mixed</Badge>}
                            
                            {theme.priority === "critical" && <Badge className="bg-red-500 hover:bg-red-600 text-white border-transparent">Critical Priority</Badge>}
                            {theme.priority === "high" && <Badge className="bg-orange-500 hover:bg-orange-600 text-white border-transparent">High Priority</Badge>}
                            {theme.priority === "medium" && <Badge className="bg-yellow-500 hover:bg-yellow-600 text-white border-transparent">Medium Priority</Badge>}
                            {theme.priority === "low" && <Badge className="bg-blue-500 hover:bg-blue-600 text-white border-transparent">Low Priority</Badge>}
                          </div>
                        </div>

                        {theme.quotes.length > 0 && (
                          <Accordion type="single" collapsible className="w-full">
                            <AccordionItem value="quotes" className="border-none">
                              <AccordionTrigger className="py-2 text-sm text-indigo-600 hover:text-indigo-700 hover:no-underline">
                                View supporting quotes
                              </AccordionTrigger>
                              <AccordionContent className="pt-2 pb-0">
                                <div className="space-y-2 border-l-2 border-indigo-200 pl-4 py-1">
                                  {theme.quotes.map((quote, qIdx) => (
                                    <p key={qIdx} className="text-sm text-slate-600 italic">"{quote}"</p>
                                  ))}
                                </div>
                              </AccordionContent>
                            </AccordionItem>
                          </Accordion>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
            
          </div>
        )}
      </div>
    </div>
  );
}
