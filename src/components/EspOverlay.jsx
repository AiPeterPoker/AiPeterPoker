import React, { useState, useEffect, useRef } from 'react';

const ZONE_COLORS = {
  player: '#4CAF50',
  community: '#FFD740',
  dealer: '#42A5F5',
};

const ZONE_LABELS = {
  player: 'PLAYER',
  community: 'COMMUNITY',
  dealer: 'DEALER',
};

export default function EspOverlay({ espData }) {
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ w: 960, h: 1080 });

  useEffect(() => {
    if (!espData || !espData.screen_w) return;
    setDimensions({ w: espData.screen_w, h: espData.screen_h });
  }, [espData]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !espData?.cards?.length) {
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const card of espData.cards) {
      const color = ZONE_COLORS[card.zone] || '#fff';
      const label = ZONE_LABELS[card.zone] || card.zone;

      // Outer glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.roundRect(card.x, card.y, card.w, card.h, 4);
      ctx.stroke();

      // Inner border (brighter)
      ctx.shadowBlur = 0;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.4;
      ctx.beginPath();
      ctx.roundRect(card.x + 3, card.y + 3, card.w - 6, card.h - 6, 2);
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // Corner brackets
      const bLen = 8;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.shadowBlur = 6;
      // Top-left
      ctx.beginPath();
      ctx.moveTo(card.x, card.y + bLen);
      ctx.lineTo(card.x, card.y);
      ctx.lineTo(card.x + bLen, card.y);
      ctx.stroke();
      // Top-right
      ctx.beginPath();
      ctx.moveTo(card.x + card.w - bLen, card.y);
      ctx.lineTo(card.x + card.w, card.y);
      ctx.lineTo(card.x + card.w, card.y + bLen);
      ctx.stroke();
      // Bottom-left
      ctx.beginPath();
      ctx.moveTo(card.x, card.y + card.h - bLen);
      ctx.lineTo(card.x, card.y + card.h);
      ctx.lineTo(card.x + bLen, card.y + card.h);
      ctx.stroke();
      // Bottom-right
      ctx.beginPath();
      ctx.moveTo(card.x + card.w - bLen, card.y + card.h);
      ctx.lineTo(card.x + card.w, card.y + card.h);
      ctx.lineTo(card.x + card.w, card.y + card.h - bLen);
      ctx.stroke();

      ctx.shadowBlur = 0;

      // Label tag
      ctx.font = 'bold 9px "Outfit", system-ui, sans-serif';
      const textW = ctx.measureText(label).width + 8;
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      ctx.roundRect(card.x, card.y - 16, textW, 14, [3, 3, 0, 0]);
      ctx.fill();
      ctx.globalAlpha = 1.0;
      ctx.fillStyle = '#0a0c10';
      ctx.fillText(label, card.x + 4, card.y - 5);
    }
  }, [espData]);

  if (!espData?.cards?.length) return null;

  return (
    <canvas
      ref={canvasRef}
      width={dimensions.w}
      height={dimensions.h}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: dimensions.w,
        height: dimensions.h,
        pointerEvents: 'none',
        zIndex: 9999,
      }}
    />
  );
}
