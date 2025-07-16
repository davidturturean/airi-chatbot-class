import './App.css'
import { Home } from './pages/home/home';
import { FullChat } from './pages/fullchat/fullchat';
import { TestPage } from './pages/test/test';

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SnippetViewer } from './pages/snippet/snippet';

function App() {
  return (
      <Router>
        <div className="w-full h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path='/chat' element={<FullChat/>}/>
            <Route path="/snippet/:snippetId" element={<SnippetViewer />} />
            <Route path="/test" element={<TestPage />} />
          </Routes>
        </div>
      </Router>
  )
}

export default App;