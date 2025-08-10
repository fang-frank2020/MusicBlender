import React, { useState, useEffect, use } from 'react';
import Landing from './Landing';
import Room from './Room';

function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [room, setRoom] = useState(null);

  return (
    <div>
      {showLanding && <Landing setRoom={setRoom} setLanding={setShowLanding}/>}
      {!showLanding && room && <Room roomId={room} setLanding={setShowLanding} />}
    </div>
  );
}

export default App;
