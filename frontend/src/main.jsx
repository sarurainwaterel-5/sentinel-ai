import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './styles/design-tokens.css'
import './styles/spacing.css'
import './styles/typography.css'
import './styles/theme.css'
import './styles/globals.css'

import App from './App.jsx'
import { DomainProvider } from './context/DomainProvider.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <DomainProvider>
      <App />
    </DomainProvider>
  </StrictMode>,
)
