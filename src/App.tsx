import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "@/components/Header";
import Landing from "@/pages/Landing";
import Analyze from "@/pages/Analyze";
import Result from "@/pages/Result";
import Taxonomy from "@/pages/Taxonomy";
import History from "@/pages/History";
import About from "@/pages/About";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background dark">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/result" element={<Result />} />
            <Route path="/taxonomy" element={<Taxonomy />} />
            <Route path="/history" element={<History />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
