import {
    combineReducers
} from 'redux';
import interactionReducer from './interactionReducer';

const rootReducer = combineReducers({
    interactions: interactionReducer,
    // Add other reducers here if your app grows
});

export default rootReducer;