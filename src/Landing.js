import React, { useState, useEffect, use } from 'react';
import './Landing.css';

function Landing({ setRoom, setLanding }) {
  const [playists, setPlaylists] = useState([]);
  const [myRooms, setmyRooms] = useState([]);
  const [me, setMe] = useState(null);
  

  function fetchPlaylists() {
    fetch('http://127.0.0.1:5000/api/message', {
      method: 'GET',
      credentials: 'include',
    })
    .then(data => data.json())
    .then((res) => {
      console.log(res);

      const playlists = res.map((playlist) => {
        return {
          name: playlist["name"],
          trackLink: playlist["tracks"]["href"]
        }
      });

      setPlaylists(playlists);
      console.log(playlists);


      // setAccessToken(res.access_token);
    })
  }

  function getUserId() {
    fetch('http://127.0.0.1:5000/api/getMe', {
      method: 'GET',
      credentials: 'include',
    })
    .then(data => data.json())
    .then((res) => {
      setMe(res.id);
      // setAccessToken(res.access_token);
    })
  }

  function createRoom() {
    fetch('http://127.0.0.1:5000/api/room', {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(data => data.json())
    .then((res) => {
      console.log(res);
      setmyRooms(res);
    })
  }

  function addPlaylistToRoom(roomId, trackLink) {
    fetch(`http://127.0.0.1:5000/api/addSongs?roomId=${roomId}&trackLink=${trackLink}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    // .then(data => data.json())
    // .then((res) => {
    //   console.log(res);
    //   //setmyRooms(res);
    // })
  }

  function addUserToRoom(user, roomId) {
    fetch(`http://127.0.0.1:5000/api/addUserToRoom?roomId=${roomId}&user=${user}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(data => data.json())
    .then((res) => {
      console.log(res);
      setmyRooms(res);
    })
  }

  useEffect(() => {
    fetchPlaylists();
    getUserId();
    // fetch('http://127.0.0.1:5000/api/login')
    // .then(data => data.json())
    // .then((res) => {
    //   console.log(res);
    //   setAccessToken(res.access_token);
    // })

    fetch('http://127.0.0.1:5000/api/readRooms')
    .then(data => data.json())
    .then((res) => {
      console.log(res);
      setmyRooms(res);
    })

  }, []);

  const handleSubmit = (e, trackLink) => {
    console.log(e);
    const roomId = e.target[0].value;
    e.preventDefault();
    addPlaylistToRoom(roomId, trackLink);
  };

  const handleAddPerson = (e, roomId) => {
    const user = e.target[0].value;
    e.preventDefault();

    addUserToRoom(user, roomId);
  }

  function goToRoom(roomId) {
    
    setRoom(roomId);
    setLanding(false);
  }




  return (
    <div className="App">
      <a href="http://127.0.0.1:5000/api/login">Login</a>
      <button onClick={() => fetchPlaylists()}>Test Fetch</button>
      <button onClick={() => createRoom()}>Create Room</button>
      {me && <p>Logged in as: {me}</p>}
      <div className="content">
        <div className="playlists">
          <h1>Spotify Playlist</h1>
          {playists.map((playlist, index) => {
            return (
              <div key={index} className="song">
                <p>{playlist["name"]} {playlist["songs"]}</p>
                <form onSubmit={(e) => handleSubmit(e, playlist["trackLink"])}>
                  <input type="text" placeholder='Room number'></input>
                  <button type="submit">Add Playlist to Room</button>
                </form>
              </div>
            );
          }
          )}
        </div>
        <div className="youtube">
        <h1>Youtube Playlist</h1>

        </div>
        <div className="rooms">
          <h1>My Rooms</h1>
          {myRooms.map((room, index) => {
            return (
              <div key={index} className="room">
                <p>Room ID: {room[0]}  People in room: {room[1]}</p>
                <button onClick={()=> goToRoom(room[0])}>View Room Details</button>
                <form onSubmit={(e) => handleAddPerson(e, room[0])}>
                  <input type="text" placeholder='spotify user id'></input>
                  <button type="submit">Add Spotify User to Room</button>
                </form>
              </div>
            );
          }
          )}
        </div>
      </div>
    </div>
  );
}

export default Landing;
