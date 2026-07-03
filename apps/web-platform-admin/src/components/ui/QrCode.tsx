import { useEffect, useState } from 'react';
import QRCode from 'qrcode';

interface QrCodeProps {
  value: string;
  className?: string;
}

export function QrCode({ value, className = '' }: QrCodeProps) {
  const [qrDataUrl, setQrDataUrl] = useState('');

  useEffect(() => {
    let isCurrent = true;
    QRCode.toDataURL(value, {
      errorCorrectionLevel: 'M',
      margin: 4,
      scale: 8,
      color: { dark: '#0F172A', light: '#FFFFFF' },
    })
      .then((dataUrl) => {
        if (isCurrent) setQrDataUrl(dataUrl);
      })
      .catch(() => {
        if (isCurrent) setQrDataUrl('');
      });
    return () => {
      isCurrent = false;
    };
  }, [value]);

  if (!qrDataUrl) {
    return <div role="img" aria-label="Authenticator setup QR code loading" className={className} />;
  }

  return <img src={qrDataUrl} role="img" alt="Authenticator setup QR code" className={className} />;
}
