import { FormEvent, useState } from 'react';
import styled from '@emotion/styled';
import { push, ref, serverTimestamp } from 'firebase/database';
import { realtimeDb } from '../../firebase.ts';

const guestbookRef = ref(realtimeDb, 'guestbook');

const CommentForm = () => {
  const [name, setName] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmedName = name.trim();
    const trimmedMessage = message.trim();

    if (!trimmedName || !trimmedMessage) {
      alert('이름과 메시지를 채워주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      await push(guestbookRef, {
        name: trimmedName,
        message: trimmedMessage,
        createdAt: serverTimestamp(),
      });

      setName('');
      setMessage('');
      alert('메시지를 보냈습니다.');
    } catch (error) {
      console.error('Failed to save guestbook message:', error);
      alert('메시지를 저장하지 못했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <FormWrapper onSubmit={handleSubmit}>
      <NameInput
        placeholder="이름"
        type="text"
        value={name}
        maxLength={29}
        disabled={isSubmitting}
        onChange={(e) => setName(e.target.value)}
      />
      <MessageInput
        placeholder="메시지"
        value={message}
        maxLength={499}
        disabled={isSubmitting}
        onChange={(e) => setMessage(e.target.value)}
      />
      <SubmitButton type="submit" disabled={isSubmitting}>
        {isSubmitting ? '등록 중' : '등록'}
      </SubmitButton>
    </FormWrapper>
  );
};

const FormWrapper = styled.form`
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: visible;
  align-items: center;
`;

const NameInput = styled.input`
  width: 100%;
  box-sizing: border-box;
  border-radius: 4px;
  padding: 4px;
  font-size: 1rem;
  line-height: 1;
  outline: none;
  border: 1px solid #ccc;
  font-family: inherit;
  font-weight: 300;
`;

const MessageInput = styled.textarea`
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  border-radius: 4px;
  padding: 4px;
  font-size: 1rem;
  line-height: 1.5;
  outline: none;
  border: 1px solid #ccc;
  resize: none;
  font-family: inherit;
  font-weight: 300;
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 1rem;
  line-height: 1.5;
  border: 1px solid lightgray;
  background-color: white;
  font-family: inherit;
  font-weight: inherit;
  color: inherit;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
`;
export default CommentForm;
