import React, { useContext } from 'react';
import { NavLink } from 'react-router-dom';

import { AuthContext } from '../../context/auth-context';
import './NavLinks.css';

const ServerLinks = ({onlogout}) => {
    const auth = useContext(AuthContext);

    const handleButtonClick = () => {
        onlogout();
        auth.logout();
    }

  return (
    <ul className="nav-links">
      <li>
        <NavLink to="/" exact>
          HOME
        </NavLink>
      </li>  
        <li>
          <NavLink to="/server">SERVER</NavLink>
        </li>
      
        <li>
          <button onClick= {handleButtonClick}>LOGOUT</button>
        </li>
    </ul>
  );
};

export default ServerLinks;
