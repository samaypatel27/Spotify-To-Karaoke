import {createContext, useState} from 'react';
import genStyle from "../styles/app.module.css";

const themeContext = createContext();

const ThemeContextProvider = ({children}) => {
    const [theme, setTheme] = useState('light');

    // call toggleTheme function to automatically set the theme
    const toggleTheme = () => {
        setTheme((current) => (current === 'light') ? 'dark' : 'light')
    }

    return (
        <themeContext.Provider value =  {{theme, toggleTheme}}>
            <section className = {(theme === 'light') ? (genStyle.light) : (genStyle.dark)}>
                {children}
            </section>
        </themeContext.Provider>
    )
}
export {ThemeContextProvider};
export default themeContext;