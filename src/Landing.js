import { useState, useEffect } from 'react';
import './Landing.css'; // Assuming you have a CSS file for styling

function Landing({ setRoom, setLanding }) {
  const [playlists, setPlaylists] = useState([]); // Spotify playlists
  const [youtubePlaylists, setYoutubePlaylists] = useState([]);
  const [myRooms, setMyRooms] = useState([]);
  const [me, setMe] = useState(null);
  const [draggedPlaylist, setDraggedPlaylist] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [toast, setToast] = useState(null);
  const [memberInputs, setMemberInputs] = useState({}); // roomId -> input value
  const [addMemberLoading, setAddMemberLoading] = useState({}); // roomId -> loading state

  // Fetch Spotify playlists
  function fetchPlaylists() {
    fetch(`/api/message`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(data => data.json())
      .then((res) => {
        if (res === null) {
          return;
        }
        const playlists = res.map((playlist) => ({
          name: playlist["name"],
          trackLink: playlist["tracks"]["href"]
        }));
        setPlaylists(playlists);
      });
    
    fetch(`/api/getYoutube`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(data => data.json())
      .then((res) => {
        if (res === null || res["data"] === null) {
          console.log('here')
          return;
        }
        console.log(res)
        setYoutubePlaylists(res["data"]);
      });
  }

  // Fetch user info
  function getUserId() {
    fetch(`/api/getMe`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(data => data.json())
      .then((res) => {
        setMe(res.id);
      });
  }

  // Fetch rooms
  function fetchRooms() {
    fetch(`/api/readRooms`, {
      credentials: 'include',
    })
      .then(data => data.json())
      .then((res) => {
        setMyRooms(res);
      });
  }

  // Create a new room
  function createRoom() {
    fetch(`/api/room`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(data => data.json())
      .then((res) => {
        setMyRooms(res);
      });
  }

  // Add Spotify playlist to a room
  function addPlaylistToRoom(roomId, trackLink) {
    fetch(`/api/addSongs?roomId=${roomId}&trackLink=${trackLink}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(() => {
        setToast('Playlist added to room!');
        setTimeout(() => setToast(null), 2000);
        fetchRooms();
      });
  }

  // Add YouTube playlist to a room
  function addYoutubePlaylistToRoom(roomId, youtubeUrl) {
    if (!roomId || !youtubeUrl) return;
    fetch(`/api/youtubeAdd?playlistId=${youtubeUrl}&roomId=${roomId}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    }).then(() => {
      setToast('YouTube playlist added to room!');
      setTimeout(() => setToast(null), 2000);
      fetchRooms();
    });
  }

  // Add member to room
  function addMemberToRoom(roomId) {
    const user = memberInputs[roomId];
    if (!user) return;
    setAddMemberLoading(l => ({ ...l, [roomId]: true }));
    fetch(`/api/addUserToRoom?roomId=${roomId}&user=${encodeURIComponent(user)}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(() => {
        setToast('Member added!');
        setTimeout(() => setToast(null), 2000);
        setMemberInputs(inputs => ({ ...inputs, [roomId]: '' }));
        setAddMemberLoading(l => ({ ...l, [roomId]: false }));
        fetchRooms();
      })
      .catch(() => {
        setToast('Failed to add member');
        setTimeout(() => setToast(null), 2000);
        setAddMemberLoading(l => ({ ...l, [roomId]: false }));
      });
  }

  // Show who I am logged in as
  function handleUserMenu() {
    setShowUserMenu(!showUserMenu);
  }

  useEffect(() => {
    fetchPlaylists();
    getUserId();
    fetchRooms();

    // eslint-disable-next-line
  }, [me]);

  function addyoutubeURL(e) {
    e.preventDefault();
    const url = e.target[0].value;
    const playListId = url.split('list=')[1];
    if (!playListId) {
      setToast('Invalid YouTube playlist URL');
      setTimeout(() => setToast(null), 2000);
      return;
    }
    
    fetch(`/api/youtubeURLAdd?playlistId=${playListId}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
    .then((res) => res.json())
    .then((res) => {
      if (res && res["data"]) {
        setYoutubePlaylists(res["data"]);
        e.target[0].value = '';
        setToast('YouTube playlist added!');
        setTimeout(() => setToast(null), 2000);
      }
    })
  }



  return (
    <div className="App">
      {/* Top Navigation Bar */}
      <div className="topbar">
        <div className="topbar-content">
          <div className="topbar-left">
            <span className="logo">MusicBlender</span>
          </div>
          <div className="topbar-right">
            {!me ? (
              <a href="api/login" className="login-btn">Login</a>
            ) : (
              <div className="user-info" onClick={handleUserMenu} tabIndex={0} style={{cursor:'pointer'}}>
                <span className="user-avatar">{me[0]}</span>
                <span className="user-id">{me}</span>
                {showUserMenu && (
                  <div className="user-menu">
                    <p>You are logged in as <b>{me}</b></p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="main-content">
        {/* Sidebar: My Rooms (Drop targets) */}
        <div className="sidebar">
          {me && 
            <div className="room-header">
              <h2>My Rooms</h2>
              <button className="create-room-btn" onClick={createRoom}>Create Room</button>
            </div>
          }
          <div className="room-list">
            {myRooms.length === 0 && <p>No rooms yet.</p>}
            {myRooms.map((room, idx) => (
              <div
                key={room[0]}
                className="room-card"
                onDragOver={e => e.preventDefault()}
                onDrop={e => {
                  e.preventDefault();
                  if (draggedPlaylist && draggedPlaylist.type === 'spotify') {
                    addPlaylistToRoom(room[0], draggedPlaylist.trackLink);
                  } else if (draggedPlaylist && draggedPlaylist.type === 'youtube') {
                    console.log(draggedPlaylist);
                    addYoutubePlaylistToRoom(room[0], draggedPlaylist.id);
                  }
                  setDraggedPlaylist(null);
                }}
                onClick={() => {
                  setRoom(room[0]);
                  setLanding(false);
                }}
                style={{ cursor: 'pointer' }}
              >
                <div>Room #{room[0]}</div>
                <div className="room-members">
                  👥 {JSON.parse(room[1]).join(', ')}
                </div>
                {/* Add member form */}
                <form
                  style={{ marginTop: 8, display: 'flex', gap: 4 }}
                  onSubmit={e => {
                    e.preventDefault();
                    addMemberToRoom(room[0]);
                  }}
                  onClick={e => e.stopPropagation()} // Prevent room navigation when clicking form
                >
                  <input
                    type="text"
                    placeholder="Add member(spotify id)"
                    value={memberInputs[room[0]] || ''}
                    onChange={e =>
                      setMemberInputs(inputs => ({
                        ...inputs,
                        [room[0]]: e.target.value,
                      }))
                    }
                    style={{ flex: 1, borderRadius: 4, border: '1px solid #ccc', padding: '2px 6px' }}
                  />
                  <button
                    type="submit"
                    disabled={addMemberLoading[room[0]]}
                    style={{
                      background: '#21a1f3',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      padding: '2px 10px',
                      cursor: 'pointer',
                    }}
                  >
                    {addMemberLoading[room[0]] ? 'Adding...' : 'Add'}
                  </button>
                </form>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Add Playlists (Draggables) - Two Columns with Icons */}
        <div className="add-playlists" style={{display:'flex', gap:32, marginTop:24}}>
          {/* Spotify Column */}
          <div style={{flex:1, background:'#eafaf1', borderRadius:12, padding:16, minWidth:220}}>
            <div style={{display:'flex', alignItems:'center', marginBottom:8}}>
              <b style={{color:'#1db954', fontSize:'1.1em'}}>Spotify</b>
            </div>
            <h3 style={{marginTop:0}}>Spotify Playlists</h3>
            {playlists.length === 0 && <p>No spotify playlists found.</p>}
            {playlists && playlists.map((playlist, idx) => (
              <div
                key={idx}
                className="playlist-card"
                draggable
                onDragStart={() => setDraggedPlaylist({ type: 'spotify', trackLink: playlist.trackLink })}
                onDragEnd={() => setDraggedPlaylist(null)}
                style={{background:'#fff', borderRadius:8, padding:'8px 12px', marginBottom:8, boxShadow:'0 1px 4px #0001'}}
              >
                <span style={{color: 'black'}}>{playlist.name}</span>
                <span style={{fontSize:'0.9em',color:'#1db954', marginLeft:8, fontWeight:500}}>Drag to Room</span>
              </div>
            ))}
          </div>
          {/* YouTube Column */}
          <div style={{flex:1, background:'#fff5f5', borderRadius:12, padding:16, minWidth:220}}>
            <div style={{display:'flex', alignItems:'center', marginBottom:8}}>
              <b style={{color:'#ff0000', fontSize:'1.1em'}}>YouTube</b>
            </div>
            <h3 style={{marginTop:0}}>Youtube Playlist Ids</h3>
            <form onSubmit={(e) => addyoutubeURL(e)}>
              <input
                type="text"
                placeholder="YouTube playlist URL"
                style={{width:'100%', padding:'8px', borderRadius:6, border:'1px solid #ddd', marginBottom:8}}
              />
            </form>
            
            {youtubePlaylists.length === 0 && <p>No youtube playlists found.</p>}
              {youtubePlaylists && youtubePlaylists.length > 0 && youtubePlaylists.map((playlist, idx) => (
                <div
                  key={idx}
                  className="playlist-card"
                  draggable
                  onDragStart={() => setDraggedPlaylist({ type: 'youtube', id: playlist })}
                  onDragEnd={() => setDraggedPlaylist(null)}
                  style={{background:'#fff', borderRadius:8, padding:'8px 12px', marginBottom:8, boxShadow:'0 1px 4px #0001'}}
                >
                  <span style={{color: 'black'}}>{playlist}</span>
                  <span style={{fontSize:'0.9em',color:'#1db954', marginLeft:8, fontWeight:500}}>Drag to Room</span>
                </div>
              ))}
          </div>
        </div>
      </div>
      {/* Toast notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: 32,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'linear-gradient(90deg, #21e672 0%, #1db954 100%)',
          color: '#fff',
          padding: '16px 40px',
          borderRadius: 12,
          boxShadow: '0 4px 24px rgba(33,161,100,0.18)',
          zIndex: 9999,
          fontSize: '1.2rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          letterSpacing: '0.5px',
        }}>
          <span style={{fontSize:'1.5em',marginRight:8}}>✔️</span>
          {toast}
        </div>
      )}
    </div>
  );
}

export default Landing;
