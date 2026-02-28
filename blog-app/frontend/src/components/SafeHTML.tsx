import React from 'react';
import DOMPurify from 'dompurify';

interface SafeHTMLProps {
  html: string;
  className?: string;
}

const SafeHTML: React.FC<SafeHTMLProps> = ({ html, className }) => {
  const token = localStorage.getItem('authToken') ?? '';
  const htmlWithTokens = html.replace(
    /src="(\/uploads\/[^?"]+)(?:\?[^"]*)?"/g,
    `src="$1?token=${token}"`
  );
  const clean = DOMPurify.sanitize(htmlWithTokens, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'h4',
      'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'a', 'img', 'video',
      'hr', 'div', 'span',
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'controls', 'width', 'height',
      'class', 'target',
    ],
  });

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: clean }}
    />
  );
};

export default SafeHTML;
