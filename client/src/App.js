import React from 'react';
import {BrowserRouter, Routes, Route} from "react-router-dom";
import Home from "./components/Home.js";
import Dashboard from "./components/Dashboard.js"
import Create from "./components/Create.js"
import Process from "./components/Process.js";
import "../node_modules/bootstrap/dist/css/bootstrap.min.css";
import '../node_modules/bootstrap/dist/js/bootstrap.bundle.min.js';
import '../node_modules/bootstrap-icons/font/bootstrap-icons.css';
import {PlaylistDataProvider} from './context/FormContext.js';
import {ThemeContextProvider} from "./context/ThemeContext.js";
import "./styles/app.module.css";


const App = () => {
  return (
    <BrowserRouter>
    <PlaylistDataProvider>
      <ThemeContextProvider>
        <Routes>
          <Route path = "/" element = {<Home />}></Route>
          <Route path = "/user/dashboard" element = {<Dashboard />}></Route>
          <Route path = "/user/create" element = {<Create />}></Route>
          <Route path = "/user/process" element = {<Process />}></Route>
        </Routes>
      </ThemeContextProvider>
    </PlaylistDataProvider>
    </BrowserRouter>

  )
}

export default App