import React, { useEffect } from 'react';
import { useHistory } from '@docusaurus/router';

const HomePageRedirect = () => {
  const history = useHistory();

  useEffect(() => {
    history.push('/2025-2A-T12-EC07-G03/introducao');
  }, [history]);

  return null;
};

export default HomePageRedirect;
