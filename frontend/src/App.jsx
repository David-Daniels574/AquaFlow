import { useState } from 'react'
import './App.css'
import './index.css'
import ConservationHub from './pages/ConservationHub.jsx'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
     <ConservationHub />
    </>
  )
}

export default App
