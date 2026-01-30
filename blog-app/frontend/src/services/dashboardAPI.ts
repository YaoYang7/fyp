import axios from 'axios';

// TODO: Put this into an ENV variable later
const API_BASE_URL = 'http://localhost:8000/api'; // Development base URL

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
  excerpt: string;
  author: string;
  author_id: number;
  date: string;
  views: number;
  comments: number;
  status: 'published' | 'draft' | 'scheduled';
  created_at?: string;
  updated_at?: string;
}

export interface DashboardStats {
  totalPosts: number;
  totalViews: number;
  totalComments: number;
  totalFollowers: number;
}

export interface CreatePostData {
  title: string;
  content: string;
  excerpt?: string;
  status: 'published' | 'draft' | 'scheduled';
}

export interface UpdatePostData {
  title?: string;
  content?: string;
  excerpt?: string;
  status?: 'published' | 'draft' | 'scheduled';
}

export const dashboardApi = {
  // Get dashboard statistics
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats');
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
  getPostComments: async (postId: number): Promise<any[]> => {
    const response = await api.get(`/posts/${postId}/comments`);
    return response.data;
  },

  // Get followers for the logged-in user
  getFollowers: async (): Promise<any[]> => {
    const response = await api.get('/user/followers');
    return response.data;
  },

  // Search posts
  searchPosts: async (query: string): Promise<BlogPost[]> => {
    const response = await api.get('/posts/search', {
      params: { q: query },
    });
    return response.data;
  },
};

export default api;