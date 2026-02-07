import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import { store } from "./store/store";
import SidePanelLayout from "./components/SidePanelLayout";
import { ProtectedRoute, GuestRoute } from "./components/RouteSettings";
import HomePage from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import AccountInfoPage from "./pages/AccountInfoPage";
import CreatePost from "./pages/CreatePost";
import Feed from "./pages/BlogHomeFeed";

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
              path="/feed"
              element={
                <ProtectedRoute>
                  <Feed />
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
