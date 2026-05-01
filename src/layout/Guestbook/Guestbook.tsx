import { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import { onValue, ref } from 'firebase/database';
import CommentForm from './CommentForm.tsx';
import { Heading2 } from '@/components/Text.tsx';
import { realtimeDb } from '../../firebase.ts';

type GuestbookMessage = {
  id: string;
  name: string;
  message: string;
  createdAt: number;
};

type GuestbookRecord = {
  name?: unknown;
  message?: unknown;
  createdAt?: unknown;
};

const dateFormatter = new Intl.DateTimeFormat('ko-KR', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

const Guestbook = () => {
  const [messages, setMessages] = useState<GuestbookMessage[]>([]);

  useEffect(() => {
    const guestbookRef = ref(realtimeDb, 'guestbook');

    const unsubscribe = onValue(
      guestbookRef,
      (snapshot) => {
        const value = snapshot.val() as Record<string, GuestbookRecord> | null;

        if (!value) {
          setMessages([]);
          return;
        }

        const nextMessages = Object.entries(value)
          .map(([id, item]) => ({
            id,
            name: typeof item.name === 'string' ? item.name : '',
            message: typeof item.message === 'string' ? item.message : '',
            createdAt: typeof item.createdAt === 'number' ? item.createdAt : 0,
          }))
          .filter(({ name, message }) => name && message)
          .sort((a, b) => b.createdAt - a.createdAt);

        setMessages(nextMessages);
      },
      (error) => {
        console.error('Failed to subscribe guestbook messages:', error);
      },
    );

    return unsubscribe;
  }, []);

  return (
    <GuestBookWrapper>
      <Heading2>
        메시지를 남겨주세요.
        <br />
        결혼식 하루 뒤, 신랑 신부에게 전달됩니다.
      </Heading2>
      <CommentForm />
      {messages.length > 0 && (
        <MessageList>
          {messages.map(({ id, name, message, createdAt }) => (
            <MessageItem key={id}>
              <MessageHeader>
                <MessageName>{name}</MessageName>
                {createdAt > 0 && (
                  <MessageDate>{dateFormatter.format(createdAt)}</MessageDate>
                )}
              </MessageHeader>
              <MessageText>{message}</MessageText>
            </MessageItem>
          ))}
        </MessageList>
      )}
    </GuestBookWrapper>
  );
};

export default Guestbook;

const GuestBookWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 50px;
`;

const MessageList = styled.ul`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  margin: 8px 0 0;
  list-style: none;
`;

const MessageItem = styled.li`
  padding: 10px 12px;
  border: 1px solid #eee;
  border-radius: 6px;
  background-color: #fff;
  text-align: left;
`;

const MessageHeader = styled.div`
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
`;

const MessageName = styled.strong`
  font-size: 0.95rem;
  font-weight: 500;
  color: #e88ca6;
  word-break: break-word;
`;

const MessageDate = styled.span`
  flex: 0 0 auto;
  font-size: 0.75rem;
  font-weight: 200;
  color: #777;
`;

const MessageText = styled.p`
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
`;
