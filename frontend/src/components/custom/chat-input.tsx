import { ArrowUp } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Textarea } from "../ui/textarea";

export default function ChatInput({
  input,
  setInput,
  handleSend,
  showDefaultOptions
}: {
  input: string;
  setInput: (value: string) => void;
  handleSend: () => void;
  showDefaultOptions: boolean;
}) {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    {
      prompt: "Summarize this conversation",
      description: "Get a concise summary of the chat so far.",
    },
    {
      prompt: "What are the next steps?",
      description: "Ask the assistant to provide action items.",
    },
    {
      prompt: "Explain this more simply",
      description: "Ask for a beginner-friendly explanation.",
    },
    {
      prompt: "List pros and cons",
      description: "Get a balanced comparison of any topic discussed.",
    },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-6 sticky bottom-0 bg-muted space-y-4">
      {/* Suggested Messages */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {showDefaultOptions && suggestions.map((s, idx) => (
          <Card
            key={idx}
            className="cursor-pointer hover:bg-accent transition p-4"
            onClick={() => setInput(s.prompt)}
          >
            <CardContent className="">
              <p className="font-medium">{s.prompt}</p>
              <p className="text-sm text-muted-foreground">{s.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chat Input */}
      <div className="flex items-end gap-2 relative">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Send a message..."
          rows={1}
          className="min-h-[100px] max-h-[200px] resize-none text-base p-3 flex-1 pb-12"
        />
        <Button className="absolute" variant="ghost" onClick={handleSend}>
            <ArrowUp size={16} className="right-0" />
        </Button>
      </div>
    </div>
  );
}
