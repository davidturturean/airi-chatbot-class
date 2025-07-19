import './App.css'
import { HomePage } from './pages/home/home';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SnippetPage } from './pages/snippet/snippet';
import { MainChatPage } from './pages/chat/mainchat';

function App() {
  return (
  <Router>
        <div className="w-full h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path='/chat' element={<MainChatPage/>}/>
            <Route path="/snippet/:fileName" element={<SnippetPage />} />
          </Routes>
        </div>
      </Router>
     
    
  )
}

export default App;