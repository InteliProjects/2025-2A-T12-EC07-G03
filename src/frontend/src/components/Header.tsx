import React from 'react';

interface HeaderProps {
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({ className = "" }) => {
  return (
    <header className={`absolute flex items-center gap-4 left-8 top-6 max-lg:gap-3 max-lg:left-6 max-lg:top-5 max-md:gap-2 max-md:left-4 max-md:top-4 max-sm:gap-2 max-sm:left-3 max-sm:top-3 ${className}`}>
      <img
        src="https://api.builder.io/api/v1/image/assets/TEMP/b05acf8f3d60338dd8fd8c1bf4ee6127c37449b6?width=186"
        alt="Flow Solutions Logo"
        className="w-[60px] h-[60px] shrink-0 aspect-square rounded-full max-lg:w-[50px] max-lg:h-[50px] max-md:w-[40px] max-md:h-[40px] max-sm:w-[35px] max-sm:h-[35px]"
      />
      <h1 className="text-[#151D48] text-2xl font-bold leading-tight max-lg:text-xl max-md:text-lg max-sm:text-base">
        Flow Solutions
      </h1>
    </header>
  );
};
