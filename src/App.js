import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [songs, setSongs] = useState([]);
  function testFetch() {
    fetch('http://127.0.0.1:5000/api/message', {
      method: 'GET',
      credentials: 'include',
    })
    .then(data => data.json())
    .then((res) => {
      console.log(res);

      const justNames = res.map((song) => {
        return {
          name: song["name"],
          trackLink: song["tracks"]["href"],
        }
      });

      setSongs(justNames);
      console.log(justNames);


      // setAccessToken(res.access_token);
    })
  }

  // useEffect(() => {
  //   fetch('http://127.0.0.1:5000/api/login')
  //   .then(data => data.json())
  //   .then((res) => {
  //     console.log(res);
  //     setAccessToken(res.access_token);
  //   })

  // }, []);
  return (
    <div className="App">
      <a href="http://127.0.0.1:5000/api/login">Login</a>
      <button onClick={() => testFetch()}>Test Fetch</button>
      <h1>Spotify Playlist</h1>
      {songs.map((song, index) => {
        return (
          <div key={index} className="song">
            <p>{song["name"]}  {song["trackLink"]}</p>
          </div>
        );
      }
      )}
    </div>
  );
}

export default App;
