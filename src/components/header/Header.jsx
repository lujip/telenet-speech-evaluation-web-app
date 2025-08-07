import React from 'react'
import './Header.css';
import Logo from '../../assets/com_logo.gif'
import { useNavigate } from 'react-router-dom';

const Header = () => {
  const navigate = useNavigate();
  
  return (
    <header className="main-header">
      <img className="logo-placeholder" src={Logo}/>
      <div className="header-links">
        <button 
          className="admin-link" 
          onClick={() => navigate('/admin')}
          title="Admin Dashboard"
        >
          Admin
        </button>
      </div>
    </header>
  )
}

export default Header