import React , {useState}  from 'react';
import {
  BrowserRouter as Router,
  Route,
  Redirect,
  Switch
} from 'react-router-dom';

import Main from './user/pages/Main';
import User from './user/pages/User';
import Server from './user/pages/server';
import MainNavigation from './shared/components/Navigation/MainNavigation';
import ServerNavigation from './shared/components/Navigation/ServerNavigation';
import { AuthContext } from './shared/context/auth-context';
import { useAuth } from './shared/hooks/auth-hook';

const App = () => {
  const { token, login, logout, userId } = useAuth();
  let routes;

  const [option, setoption] = useState (true);

  const handleoptionchange = () =>{
    if(option === true){
      setoption(false);
    }
    else{
      setoption(true);
    }
  }

  if(token) {
    routes = (
      <Switch>
        <Route path="/" exact>
          <Main />
        </Route>
        <Route path="/server">
          <Server onOptionchange = {handleoptionchange} />
        </Route>
        <Redirect to="/" />
      </Switch>
    );
  } 
  else {
    routes = (
      <Switch>
        <Route path="/" exact>
          <Main />
        </Route>
        <Route path="/user">
          <User onOptionchange = {handleoptionchange}/>
        </Route>
        <Redirect to="/" />
      </Switch>
    );
  }

  return (
      <AuthContext.Provider
        value={{
          userLoggedIn: !!token,
          token: token,
          userId: userId,
          login: login,
          logout:logout,
        }}
      >
        <Router>
          {option === true  && (<MainNavigation />)}
          {option === false  && (<ServerNavigation onOptionchange = {handleoptionchange}/>)}
          <main>{routes}</main>
        </Router>
      </AuthContext.Provider> 
  );
};

export default App;


// try:
    // with open('/Server.json') as f:
    //     x = json.load(f)
// except:
//     print('server file not found')
