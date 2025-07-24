import {
    configureStore
} from '@reduxjs/toolkit';
// import { thunk } from 'redux-thunk'; // <--- REMOVE OR COMMENT OUT THIS LINE
import rootReducer from './reducers';

const store = configureStore({
    reducer: rootReducer,
    // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(thunk), // <--- REMOVE OR COMMENT OUT THIS ENTIRE LINE
    // configureStore automatically adds redux-thunk by default,
    // so no need to explicitly add it unless you have other custom middleware.
    devTools: process.env.NODE_ENV !== 'production', // Enable Redux DevTools only in development
});

export default store;