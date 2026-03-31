import axios from 'axios';

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authorization token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export interface BlogPost {
  id: number;
  title: string;
  content: string;
  summary: string;
  author: string;
  author_id: number;
  date: string;
  comments: number;
  status: 'published' | 'draft';
  created_at?: string;
  updated_at?: string;
}

export interface DashboardStats {
  totalPosts: number;
  totalComments: number;
}

export interface Comment {
  id: number;
  content: string;
  author: string;
  author_id: number;
  post_id: number;
  created_at: string;
  updated_at?: string;
}

export interface CreatePostData {
  title: string;
  content: string;
  summary?: string;
  status: 'published' | 'draft';
}

export interface UpdatePostData {
  title?: string;
  content?: string;
  summary?: string;
  status?: 'published' | 'draft';
}

export interface GroupUser {
  id: number;
  username: string;
  email: string;
  created_at: string;
  published_posts: number;
}

export interface PublicTenant {
  id: number;
  name: string;
  slug: string;
}

export interface PublicPost extends BlogPost {
  tenant_id: number;
  tenant_name: string;
}

export const dashboardApi = {
  // Get dashboard statistics
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Get all published posts in the tenant (feed)
  getFeedPosts: async (limit: number = 50): Promise<BlogPost[]> => {
    const response = await api.get('/posts/feed', {
      params: { limit },
    });
    return response.data;
  },

  // Get recent posts for the logged-in user
  getRecentPosts: async (limit: number = 10): Promise<BlogPost[]> => {
    const response = await api.get('/posts/recent', {
      params: { limit },
    });
    return response.data;
  },

  // Get all posts for the logged-in user
  getUserPosts: async (): Promise<BlogPost[]> => {
    const response = await api.get('/posts/user');
    return response.data;
  },

  // Get a single post by ID
  getPost: async (postId: number): Promise<BlogPost> => {
    const response = await api.get(`/posts/${postId}`);
    return response.data;
  },

  // Create a new blog post
  createPost: async (data: CreatePostData): Promise<BlogPost> => {
    const response = await api.post('/posts', data);
    return response.data;
  },

  // Update an existing blog post
  updatePost: async (postId: number, data: UpdatePostData): Promise<BlogPost> => {
    const response = await api.put(`/posts/${postId}`, data);
    return response.data;
  },

  // Delete a blog post
  deletePost: async (postId: number): Promise<void> => {
    await api.delete(`/posts/${postId}`);
  },

  // Get comments for a specific post
  getPostComments: async (postId: number): Promise<Comment[]> => {
    const response = await api.get(`/posts/${postId}/comments`);
    return response.data;
  },

  // Create a new comment on a post
  createComment: async (postId: number, content: string): Promise<Comment> => {
    const response = await api.post(`/posts/${postId}/comments`, {
      content,
      post_id: postId,
    });
    return response.data;
  },

  // Delete a comment
  deleteComment: async (postId: number, commentId: number): Promise<void> => {
    await api.delete(`/posts/${postId}/comments/${commentId}`);
  },

  // Upload a file (image or video)
  uploadFile: async (file: File): Promise<{ url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Search posts
  searchPosts: async (query: string): Promise<BlogPost[]> => {
    const response = await api.get('/posts/search', {
      params: { q: query },
    });
    return response.data;
  },

  // Get all users in the same group (tenant)
  getGroupUsers: async (): Promise<GroupUser[]> => {
    const response = await api.get('/users');
    return response.data;
  },

  // Public endpoints (no auth required)
  getPublicTenants: async (): Promise<PublicTenant[]> => {
    const response = await api.get('/public/tenants');
    return response.data;
  },

  getPublicPosts: async (tenantId?: number, limit: number = 50): Promise<PublicPost[]> => {
    const response = await api.get('/public/posts', {
      params: { tenant_id: tenantId, limit },
    });
    return response.data;
  },

  getPublicPost: async (postId: number): Promise<PublicPost> => {
    const response = await api.get(`/public/posts/${postId}`);
    return response.data;
  },
};

export default api;