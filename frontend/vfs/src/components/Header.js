
import React from 'react';
import logo from '../assets/logo.png';

const Header = () => {
    
    return (
        <div className="bg-black text-white flex justify-between items-center p-8 rounded-3xl shadow-xl max-w-4xl mx-auto w-full">
            <img src={logo} alt='VFS Logo' className="w-[100px] h-auto" />
            <ul className="list-none flex gap-5 text-sm">
                <li><a href="#" className="text-white no-underline mx-2">Home</a></li>
                <li><a href="#" className="text-gray-400 no-underline mx-2">Pricing</a></li>
                <li><a href="#" className="text-gray-400 no-underline mx-2">Contact Us</a></li>
            </ul>
        </div>
    );
};

export default Header;
