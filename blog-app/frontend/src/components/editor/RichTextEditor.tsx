import React, { useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import { Box, IconButton, Divider, Tooltip } from '@mui/material';
import {
  FormatBold,
  FormatItalic,
  FormatStrikethrough,
  Code,
  FormatListBulleted,
  FormatListNumbered,
  FormatQuote,
  HorizontalRule,
  Undo,
  Redo,
  Image as ImageIcon,
  VideoLibrary,
  Title,
} from '@mui/icons-material';
import { Video } from './VideoExtension';
import { dashboardApi } from '../../services/dashboardAPI';
import * as styles from './RichTextEditorStyles';

interface RichTextEditorProps {
  content: string;
  onChange: (html: string) => void;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ content, onChange }) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({ inline: false, allowBase64: false }),
      Video,
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  const handleFileUpload = useCallback(
    async (file: File, type: 'image' | 'video') => {
      if (!editor) return;
      try {
        const { url } = await dashboardApi.uploadFile(file);
        const backendUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
        const fullUrl = `${backendUrl}${url}`;
        if (type === 'image') {
          editor.chain().focus().setImage({ src: fullUrl }).run();
        } else {
          editor
            .chain()
            .focus()
            .insertContent({
              type: 'video',
              attrs: { src: fullUrl },
            })
            .run();
        }
      } catch (err) {
        console.error('Upload failed:', err);
      }
    },
    [editor]
  );

  const triggerFileInput = (accept: string, type: 'image' | 'video') => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) handleFileUpload(file, type);
    };
    input.click();
  };

  if (!editor) return null;

  return (
    <Box sx={styles.editorContainer}>
      {/* Toolbar */}
      <Box sx={styles.toolbar}>
        <Tooltip title="Bold">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleBold().run()}>
            <FormatBold />
          </IconButton>
        </Tooltip>
        <Tooltip title="Italic">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleItalic().run()}>
            <FormatItalic />
          </IconButton>
        </Tooltip>
        <Tooltip title="Strikethrough">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleStrike().run()}>
            <FormatStrikethrough />
          </IconButton>
        </Tooltip>
        <Tooltip title="Code">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleCode().run()}>
            <Code />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={styles.toolbarDivider} />
        <Tooltip title="Heading">
          <IconButton
            size="small"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          >
            <Title />
          </IconButton>
        </Tooltip>
        <Tooltip title="Bullet List">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleBulletList().run()}>
            <FormatListBulleted />
          </IconButton>
        </Tooltip>
        <Tooltip title="Ordered List">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleOrderedList().run()}>
            <FormatListNumbered />
          </IconButton>
        </Tooltip>
        <Tooltip title="Blockquote">
          <IconButton size="small" onClick={() => editor.chain().focus().toggleBlockquote().run()}>
            <FormatQuote />
          </IconButton>
        </Tooltip>
        <Tooltip title="Horizontal Rule">
          <IconButton size="small" onClick={() => editor.chain().focus().setHorizontalRule().run()}>
            <HorizontalRule />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={styles.toolbarDivider} />
        <Tooltip title="Insert Image">
          <IconButton size="small" onClick={() => triggerFileInput('image/*', 'image')}>
            <ImageIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Insert Video">
          <IconButton size="small" onClick={() => triggerFileInput('video/*', 'video')}>
            <VideoLibrary />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem sx={styles.toolbarDivider} />
        <Tooltip title="Undo">
          <IconButton size="small" onClick={() => editor.chain().focus().undo().run()}>
            <Undo />
          </IconButton>
        </Tooltip>
        <Tooltip title="Redo">
          <IconButton size="small" onClick={() => editor.chain().focus().redo().run()}>
            <Redo />
          </IconButton>
        </Tooltip>
      </Box>
      {/* Editor area */}
      <Box sx={styles.editorArea}>
        <EditorContent editor={editor} />
      </Box>
    </Box>
  );
};

export default RichTextEditor;
