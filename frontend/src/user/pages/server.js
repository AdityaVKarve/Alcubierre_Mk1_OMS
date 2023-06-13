import React from 'react';
import { useState,useEffect } from 'react';
import { useHistory } from 'react-router-dom';

// import background from './background.jpg'
import './Main.css';
import Button from '../../shared/components/FormElements/Button';
import Card from '../../shared/components/UIElements/Card';

const Server = ({onOptionchange}) => {
  const history = useHistory();
  const handleButtonClick = () =>{
    onOptionchange();
    history.push('/');
  }

  return (
    <React.Fragment>
      <div className="center">
      <h1 style={{ color: 'white' }}>CHOOSE A SERVER</h1>
    </div>
    <div className='center'>
      <Card>
      <h3 style={{ margin : '20px 40px' }}>Live Server</h3>

        <Button danger onClick={handleButtonClick} >LIVE</Button>
      </Card>
      <p></p>
    </div>
    <p></p>
    <div className='center'>
      <Card>
        <h3>Development Server</h3>
        <Button danger onClick={handleButtonClick} >DEVELOPMENT</Button>
      </Card>
    </div>
    </React.Fragment>
  );
};

export default Server;
