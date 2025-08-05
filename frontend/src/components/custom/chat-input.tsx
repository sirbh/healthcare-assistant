import { ArrowUp } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Textarea } from "../ui/textarea";
import { useContext, useState } from "react";
import { MessageStateContext } from "@/context/message-state";

// export default function ChatInput({
//   input,
//   setInput,
//   handleSend,
//   showDefaultOptions,
//   loading
// }: {
//   input: string;
//   setInput: (value: string) => void;
//   handleSend: () => void;
//   showDefaultOptions: boolean;
//   loading: boolean;
// }) {

export default function ChatInput() {

  const {updateMessage,messagesLoading, messages, messageLoading} = useContext(MessageStateContext);
  const [input, setInput] = useState<string>("");

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        updateMessage(input);
        setInput("");
      }
    }
  };

const suggestions = [
  {
    prompt: "I am feeling dizzy?",
    description: "Get possible causes and advice for dizziness.",
  },
  {
    prompt: "I am experiencing a headache?",
    description: "Understand common reasons for headaches and when to be concerned.",
  },
  {
    prompt: "I am having chest pain?",
    description: "Find out if your chest pain could be serious and what to do next.",
  },
  {
    prompt: "I am experiencing weird stomach pain?",
    description: "Explore possible reasons for unusual stomach discomfort.",
  },
];

  return (
    <div className="w-full max-w-2xl mx-auto px-4 py-6 sticky bottom-0 bg-muted space-y-4">
      {/* Suggested Messages */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {!messagesLoading && messages.length===0 && suggestions.map((s, idx) => (
          <Card
            key={idx}
            className="cursor-pointer hover:bg-accent transition p-4"
            onClick={() => {
              updateMessage(s.prompt);
            }}
          >
            <CardContent className="">
              <p className="font-medium">{s.prompt}</p>
              <p className="text-sm text-muted-foreground">{s.description}</p>
            </CardContent>
          </Card>
        ))}
        {messagesLoading && suggestions.map((s, idx) => (
          <Card
            key={idx}
            className="transition p-4 flex animate-pulse space-x-4"
          >
            <CardContent className="">
              <div className="flex-1 space-y-6 py-1">
                <div className="h-2 rounded bg-gray-200"></div>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 h-2 rounded bg-gray-200"></div>
                    <div className="col-span-1 h-2 rounded bg-gray-200"></div>
                  </div>
                  <div className="h-2 rounded bg-gray-200"></div>
                </div>
              </div>
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
          disabled={messageLoading||messagesLoading}
        />
        <Button className="absolute" variant="ghost" onClick={()=>{
          if (input.trim()) {
            updateMessage(input);
            setInput("");
          }
        }} disabled={messageLoading||messagesLoading}>
          <ArrowUp size={16} className="right-0" />
        </Button>
      </div>
    </div>
  );
}
