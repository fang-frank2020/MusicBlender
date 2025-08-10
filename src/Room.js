import React, { useState, useEffect, use } from 'react';
import './Room.css';

function Room({ roomId, setLanding }) {
  const [songs, setSongs] = useState(null);
  const [generatedPlaylist, setGeneratedPlaylist] = useState(null);
  
  function backLanding() {
    setLanding(true);
  }

  function generatePlayList() {
    console.log("Generating playlist for room:", roomId);
    fetch(`http://127.0.0.1:5000/api/generate?roomId=${roomId}&numSongs=${20}`)
    .then(data => data.json())
    .then((res) => {
      console.log(res);
      setGeneratedPlaylist(res.data);
    })
  }

  useEffect(() => {
    fetch(`http://127.0.0.1:5000/api/getSongs?roomId=${roomId}`, {
      method: 'GET',
      credentials: 'include',
    })
    .then(data => data.json())
    .then((res) => {
      console.log(res.songs);
      setSongs(res.songs);
      console.log("Songs in room:", songs);

      // setAccessToken(res.access_token);
    })
  }, [roomId]);

  return (
    <div className="Room">
      <button onClick={() => backLanding()}>Go Back</button>
      <h1>Room</h1>
      {songs && songs.length > 0 && <button onClick={() => {generatePlayList()}}>Generate a new playlist of songs</button>}
      <div className="roomBottom">
        <div>
          {generatedPlaylist && generatedPlaylist.length > 0 && (
            generatedPlaylist.map((song, index) => (
              <div key={index}>
                <p>{song[0]} - {song[1] && song[1].map((artist, indexArtist) => {
                  return <span key={indexArtist}>{artist}{index < song[1].length - 1 ? ', ' : ''}</span>;
                })}
                </p> 
              </div>
            ))
          )}
        </div>

        <div className="existing">
          {songs && songs.length > 0 && (
            songs.map((song, index) => (
              <div key={index}>
                <p>{song[0]} - {song[1] && song[1].map((artist, indexArtist) => {
                  return <span key={indexArtist}>{artist}{indexArtist < song[1].length - 1 ? ', ' : ''}</span>;
                })}
                </p> 
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default Room;
