
import { useState } from 'react';
import { Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import AppSidebar from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I'm your AI assistant. How can I help you today?", sender: 'bot' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSendMessage = async () => {
    if (inputMessage.trim() && !isLoading) {
      const newMessage = {
        id: messages.length + 1,
        text: inputMessage,
        sender: 'user' as const
      };
      setMessages([...messages, newMessage]);
      const currentInput = inputMessage;
      setInputMessage('');
      setIsLoading(true);
      
      try {
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
          toast({
            title: "Authentication Error",
            description: "Please login again to continue.",
            variant: "destructive"
          });
          return;
        }

        console.log('Sending request to http://127.0.0.1:8000/conversational-bi with payload:', { user_input: currentInput });
        
        const response = await fetch('http://127.0.0.1:8000/conversational-bi', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          },
          body: JSON.stringify({
            user_input: currentInput
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response from http://127.0.0.1:8000/conversational-bi:', data);
        
        const botResponse = {
          id: messages.length + 2,
          text: data.message || "I received your message but couldn't process it properly.",
          sender: 'bot' as const
        };
        setMessages(prev => [...prev, botResponse]);
      } catch (error) {
        console.error('Error calling conversational-bi endpoint:', error);
        toast({
          title: "Error",
          description: "Failed to get response from AI assistant. Please try again.",
          variant: "destructive"
        });
        
        const errorResponse = {
          id: messages.length + 2,
          text: "Sorry, I'm having trouble processing your request right now. Please try again.",
          sender: 'bot' as const
        };
        setMessages(prev => [...prev, errorResponse]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSendMessage();
    }
  };

  // Function to convert \n to actual line breaks and prepare text for markdown
  const formatMessageText = (text: string) => {
    return text.replace(/\\n/g, '\n');
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gray-50">
        <AppSidebar />
        <SidebarInset>
          <main className="flex-1 p-6">
            <div className="max-w-4xl mx-auto h-full">
              <h1 className="text-3xl font-bold text-gray-900 mb-6">AI Assistant</h1>
              
              <div className="bg-white rounded-lg shadow-lg h-[calc(100vh-200px)] flex flex-col">
                {/* Chat Messages */}
                <div className="flex-1 p-6 overflow-y-auto">
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            message.sender === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {message.sender === 'bot' ? (
                            <div className="prose prose-sm max-w-none text-gray-800">
                              <ReactMarkdown
                                components={{
                                  h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2 text-gray-800" {...props} />,
                                  h2: ({node, ...props}) => <h2 className="text-base font-semibold mb-2 text-gray-800" {...props} />,
                                  h3: ({node, ...props}) => <h3 className="text-sm font-medium mb-1 text-gray-800" {...props} />,
                                  p: ({node, ...props}) => <p className="mb-2 last:mb-0 text-gray-800" {...props} />,
                                  ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                  ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                  li: ({node, ...props}) => <li className="mb-1 text-gray-800" {...props} />,
                                  strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                                  em: ({node, ...props}) => <em className="italic text-gray-800" {...props} />,
                                  code: ({node, ...props}) => <code className="bg-gray-200 px-1 py-0.5 rounded text-sm text-gray-900" {...props} />,
                                  pre: ({node, ...props}) => <pre className="bg-gray-200 p-2 rounded text-sm overflow-x-auto text-gray-900" {...props} />,
                                }}
                              >
                                {formatMessageText(message.text)}
                              </ReactMarkdown>
                            </div>
                          ) : (
                            message.text
                          )}
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                            <span>AI is thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Input Area */}
                <div className="border-t p-4">
                  <div className="flex space-x-2">
                    <Input
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your message..."
                      className="flex-1"
                      disabled={isLoading}
                    />
                    <Button onClick={handleSendMessage} className="px-4" disabled={isLoading}>
                      <Send size={20} />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default Chatbot;
