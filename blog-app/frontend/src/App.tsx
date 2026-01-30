import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import { store } from "./store/store";
import SidePanelLayout from "./components/SidePanelLayout";
import { ProtectedRoute, GuestRoute } from "./components/RouteSettings";
import HomePage from "./pages/Home";
import Dashboard from "./pages/Dashboard";

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
          </Routes>
        </SidePanelLayout>
      </BrowserRouter>
    </Provider>
  );
}

export default App;
