import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';

import './App.css';

import React, { Component } from 'react';
import Hls from 'hls.js';

import API from './API';

const AppState = {
    PLAYLISTS: "playlists",
    TRACKS: "tracks",
}

class Playlist extends Component {
    constructor(props) {
        super(props);
        this.handleLoadPlaylist = this.handleLoadPlaylist.bind(this);
    }
    
    handleLoadPlaylist(e) {
        e.preventDefault();
        this.props.onLoadPlaylist(this.props.playlist);
    }
    
    render() {
        const playlist = this.props.playlist;
        return (
            <div className="col-md-3">
              <div className="panel panel-default">
                <div className="panel-body">
                  <p>{playlist.name}</p>
                  <p><em>Now:</em> {playlist.scheduled[0].track.artist} - {playlist.scheduled[0].track.title}</p>
                  <p><em>Next:</em> {playlist.scheduled[1].track.artist} - {playlist.scheduled[1].track.title}</p>
                  <p><a href={playlist.url} onClick={this.handleLoadPlaylist}>Listen Now!</a></p>
                </div>
              </div>
            </div>
        );
    }
}

function PlaylistRow(props) {
    var items = [];
    for (var i=0; i<props.row.length; i++) {
        items.push(
                <Playlist key={props.row[i].id} playlist={props.row[i]} onLoadPlaylist={props.onLoadPlaylist}/>
        );
    }
    return (
        <div className="row">
            {items}
        </div>
    );
}

class PlaylistsList extends Component {
    constructor(props) {
        super(props);
        this.state = {playlists: null};
        this.handlePlaylists = this.handlePlaylists.bind(this);
    }
    componentDidMount() {
        API.getPlaylists(this.handlePlaylists);
    }
    handlePlaylists(r) {
        if (r.status === "ok")
            this.setState({playlists: r.playlists});
    }
    render() {
        var rows = [];
        if (this.state.playlists) {
            for (var i=0; i<this.state.playlists.length; i+=3) {
                var slice = this.state.playlists.slice(i, i+3);
                rows.push(
                        <PlaylistRow key={i} row={slice} onLoadPlaylist={this.props.onLoadPlaylist}/>
                );
            }
        }

        return (
            <div className="container-fluid">
                {rows}    
            </div>
        );
    }   
}


class App extends Component {
    
    constructor(props) {
        super(props);
        this.state = {status: null, selected: AppState.PLAYLISTS};
        this.handleStatus = this.handleStatus.bind(this);
        this.handleStatusError = this.handleStatusError.bind(this);
        this.select = this.select.bind(this);
        this.selectPlaylists = this.selectPlaylists.bind(this);
        this.selectTracks = this.selectTracks.bind(this);
        this.handleLoadPlaylist = this.handleLoadPlaylist.bind(this);
    }
    
    componentDidMount() {
        API.checkStatus(this.handleStatus, this.handleStatusError);
    }

    select(e, selected) {
        e.preventDefault();
        this.setState({selected: selected});
    }
    
    selectPlaylists(e) {
        this.select(e, AppState.PLAYLISTS);
    }

    selectTracks(e) {
        this.select(e, AppState.TRACKS);
    }

    handleStatus(r) {
        this.setState({status: true});
    }

    handleStatusError(r) {
        this.setState({status: false});
    }

    handleLoadPlaylist(playlist) {
        console.log("play", playlist);
        if (Hls.isSupported()) {
            var player = document.getElementById("player");
            var hls = new Hls({
                debug: true,
                liveSyncDurationCount: 10
            });
            hls.attachMedia(player);
            hls.on(Hls.Events.MEDIA_ATTACHED, function () {
		        console.log("attached");

                hls.loadSource(playlist.url);
                hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
                    console.log("manifest loaded, found " + data.levels.length + " quality level");
                    player.play();
                });
                

            });
        } else {
            console.log("hls not supported");
        }
    }
    
    render() {

        let body = null;
        if (this.state.selected === AppState.PLAYLISTS) {
            body = <PlaylistsList onLoadPlaylist={this.handleLoadPlaylist}/>;
        } else if (this.state.selected === AppState.TRACKS) {
        }
        
        return (            
            <div>
                <nav className="navbar navbar-default navbar-fixed-top">
                    <div className="container-fluid">
                        <ul className="nav navbar-nav">
                            <li><a href="#" onClick={this.selectPlaylists}>Playlists</a></li>
                            <li><a href="#" onClick={this.selectTracks}>Tracks</a></li>
                        </ul>
                    </div>
                </nav>
                {body}
                <video id="player"/>
            </div>
        );
    }
}

export default App;
