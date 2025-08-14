import React, { useState, useEffect } from 'react';
import './Room.css'; // Assuming you have a CSS file for styling

function Room({ roomId, setLanding }) {
  const [songs, setSongs] = useState(null);
  const [generatedPlaylist, setGeneratedPlaylist] = useState(null);
  const [generatedPlaylistName, setGeneratedPlaylistName] = useState("");


  function backLanding() {
    setLanding(true);
  }

  function generatePlayList() {
    fetch(`/api/generate?roomId=${roomId}&numSongs=${20}`)
      .then(data => data.json())
      .then((res) => {
        setGeneratedPlaylist(res.data);
      })
  }

  useEffect(() => {
  fetch(`/api/getSongs?roomId=${roomId}`)
    .then(res => res.json())
    .then(res => {
      console.log("Fetched songs:", res);
      if (res.error) {
        console.error(res.error);
        return;
      }
      setSongs(res.songs);
    })
    .catch(err => {
      console.error("Error fetching songs:", err);
    });
  }, [roomId]);

  function createPlaylist() {
    fetch(`/api/exportGeneratedPlaylist?name=${generatedPlaylistName}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ songs: generatedPlaylist }),
      }
    )
    .then(res => res.json())
    .then(res => {
      console.log("Fetched songs:", res);
      if (res.error) {
        console.error(res.error);
        return;
      }
      setSongs(res.songs);
    })
    .catch(err => {
      console.error("Error fetching songs:", err);
    });
  }

  return (
    <div className="Room">
      <button onClick={() => backLanding()}>Go Back</button>
      <h1>Room {roomId}</h1>
      <div className="buttons">
        {songs && songs.length > 0 && <button onClick={() => {generatePlayList()}}>Generate a new playlist of songs</button>}
        {generatedPlaylist && generatedPlaylist.length > 0 &&
          <div className='generated-playlistFields'>
            <form className='generated-playlistForm'>
              <input type="text" placeholder="Name of Generated Playlist" value={generatedPlaylistName} onChange={(e) => setGeneratedPlaylistName(e.target.value)} />
            </form>
            <button disabled={generatedPlaylistName == null || generatedPlaylistName == ""} onClick={() => {createPlaylist()}}>Export generated playlist to spotify</button>
          </div>
        }
      </div>
      <div className="roomBottom">
        <div className="existing">
          <h1>Existing Songs</h1>
          {songs && songs.length > 0 && (
            songs.map((song, index) => {
              return (
                <div key={index} style={{position:'relative'}}>
                  <p>
                    {song[0]} - {song[1] && song[1].map((artist, indexArtist) => {
                      return <span key={indexArtist}>{artist}{indexArtist < song[1].length - 1 ? ', ' : ''}</span>;
                    })}
                  </p>
                </div>
              );
            })
          )}
        </div>

        <div className="generated">
          <h1>Generated Playlist</h1>
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
      </div>
    </div>
  );
}

export default Room;
