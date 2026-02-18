import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import { store } from "./store/store";
import SidePanelLayout from "./components/SidePanelLayout";
import { ProtectedRoute, GuestRoute } from "./components/RouteSettings";
import HomePage from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import AccountInfoPage from "./pages/AccountInfoPage";
import CreatePost from "./pages/CreatePost";
import ManageBlog from "./pages/ManageBlog";
import EditPost from "./pages/EditPost";
import GroupBlogFeeds from "./pages/GroupBlogFeeds";
import ViewPost from "./pages/ViewPost";

function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <SidePanelLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route
              path="/home"
              element={
                <GuestRoute>
                  <HomePage />
                </GuestRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account_info"
              element={
                <ProtectedRoute>
                  <AccountInfoPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/create_post"
              element={
                <ProtectedRoute>
                  <CreatePost />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage_blog"
              element={
                <ProtectedRoute>
                  <ManageBlog />
                </ProtectedRoute>
              }
            />
            <Route
              path="/edit_post/:id"
              element={
                <ProtectedRoute>
                  <EditPost />
                </ProtectedRoute>
              }
            />
            <Route
              path="/feed"
              element={
                <ProtectedRoute>
                  <GroupBlogFeeds />
                </ProtectedRoute>
              }
            />
            <Route
              path="/post/:id"
              element={
                <ProtectedRoute>
                  <ViewPost />
                </ProtectedRoute>
              }
            />
          </Routes>
        </SidePanelLayout>
      </BrowserRouter>
    </Provider>
  );
}

export default App;
