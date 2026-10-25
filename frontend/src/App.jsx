import { useEffect, useState } from 'react';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import HomePage from './pages/HomePage.jsx';
import DepressionAssessment from './pages/DepressionAssessment.jsx';
import SchizophreniaAssessment from './pages/SchizophreniaAssessment.jsx';
import BipolarAssessment from './pages/BipolarAssessment.jsx';
import AnxietyAssessment from './pages/AnxietyAssessment.jsx';
import ModulePlaceholder from './pages/ModulePlaceholder.jsx';

function currentPath() {
  return window.location.pathname.replace(/\/$/, '') || '/';
}

export default function App() {
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    const updatePath = () => setPath(currentPath());
    window.addEventListener('popstate', updatePath);
    return () => window.removeEventListener('popstate', updatePath);
  }, []);

  const slug = path.slice(1);
  const isHome = path === '/';

  useEffect(() => {
    if (isHome && window.location.hash) {
      requestAnimationFrame(() => document.querySelector(window.location.hash)?.scrollIntoView());
    } else if (!isHome) {
      window.scrollTo(0, 0);
    }
  }, [isHome, path]);

  return (
    <>
      <Navbar />
      {isHome ? (
        <HomePage />
      ) : path === '/depression' ? (
        <DepressionAssessment />
      ) : path === '/schizophrenia' ? (
        <SchizophreniaAssessment />
      ) : path === '/bipolar' ? (
        <BipolarAssessment />
      ) : path === '/anxiety' ? (
        <AnxietyAssessment />
      ) : (
        <ModulePlaceholder slug={slug} />
      )}
      <Footer />
    </>
  );
}
