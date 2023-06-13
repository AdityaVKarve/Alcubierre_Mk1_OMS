import { createContext } from 'react';

export const AuthContext = createContext({
  userLoggedIn: false,
  userId: null,
  token: null,
  login: () => {},
  logout: () => {}
});
