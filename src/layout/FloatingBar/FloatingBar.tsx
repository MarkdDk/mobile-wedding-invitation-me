import { useEffect, useMemo, useState } from 'react';
import styled from '@emotion/styled';
import data from 'data.json';
import { onValue, ref, runTransaction } from 'firebase/database';
import JSConfetti from 'js-confetti';
import Heart from '@/assets/icons/heart_plus.svg?react';
import Share from '@/assets/icons/share.svg?react';
import Upward from '@/assets/icons/upward.svg?react';
import Button from '@/components/Button.tsx';
import { realtimeDb } from '../../firebase.ts';

const FloatingBar = ({ isVisible }: { isVisible: boolean }) => {
  const { emojis } = data;
  const [count, setCount] = useState(0);
  const jsConfetti = useMemo(() => new JSConfetti(), []);

  useEffect(() => {
    const likesRef = ref(realtimeDb, 'likes/count');

    const unsubscribe = onValue(
      likesRef,
      (snapshot) => {
        setCount(Number(snapshot.val() ?? 0));
      },
      (error) => {
        console.error('Failed to subscribe likes:', error);
      },
    );

    return unsubscribe;
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(window.location.href).then(
      () => {
        alert('주소가 복사되었습니다.😉😉');
      },
      () => {
        alert('주소 복사에 실패했습니다.🥲🥲');
      },
    );
  };

  const handleCount = () => {
    void jsConfetti.addConfetti({ emojis });

    void runTransaction(ref(realtimeDb, 'likes/count'), (current) => {
      return Number(current ?? 0) + 1;
    }).catch((error) => {
      console.error('Failed to update likes:', error);
      alert('좋아요를 저장하지 못했습니다. 잠시 후 다시 시도해주세요.');
    });
  };

  const handleScroll = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Nav isVisible={isVisible}>
      <Button onClick={handleCount}>
        <Heart fill="#e88ca6" />
        {count || ''}
      </Button>
      <Button onClick={handleCopy}>
        <Share fill="#e88ca6" />
        공유
      </Button>
      <Button onClick={handleScroll}>
        <Upward fill="#e88ca6" />
        위로
      </Button>
    </Nav>
  );
};

export default FloatingBar;

const Nav = styled.nav<{ isVisible: boolean }>`
  min-width: 280px;
  position: fixed;
  bottom: 30px;
  left: 0;
  right: 0;
  align-items: center;
  justify-content: center;
  gap: 5px;
  display: ${(props) => (props.isVisible ? 'flex' : 'none')};
`;
