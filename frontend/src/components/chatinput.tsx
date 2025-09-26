import { Textarea } from "../ui/textarea";
import { cx } from 'classix';
import { ArrowUpIcon } from "./icons"
import { toast } from 'sonner';
import { ChatInputProps } from '../interfaces/interfaces'
import { InfoTooltip } from './info-tooltip';

export const ChatInput = ({ question, setQuestion, onSubmit, isLoading }: ChatInputProps) => {

    return(
    <div className="relative w-full flex flex-col gap-4">
     <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">Ask about AI risks</span>
        <InfoTooltip content="Try questions like: 'What are the privacy risks of facial recognition?' or 'How does AI affect employment?' The assistant searches our database of documented AI risks to provide evidence-based answers." />
     </div>

        <Textarea
        placeholder="Send a message..."
        className={cx(
            'min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none rounded-xl text-base bg-muted',
        )}
        value={question}
        //updates the question inside the box
        onChange={(e) => setQuestion(e.target.value)}
        //press enter --> goes to backend
        onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();

                if (isLoading) {
                    toast.error('Please wait for the model to finish its response!');
                } else {
                    onSubmit(question);
                    setQuestion("");
                }
            }
        }}
        rows={3}
        autoFocus
        />

        <button 
            className="rounded-full p-1.5 h-fit absolute bottom-2 right-2 m-0.5 border dark:border-zinc-600"
            onClick={() => {
                onSubmit(question);
                setQuestion("");
            }}
            disabled={question.length === 0}
        >
            <ArrowUpIcon size={14} />
        </button>
    </div>
    );
}


