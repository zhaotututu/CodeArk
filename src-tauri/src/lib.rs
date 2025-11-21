use tauri::{
    menu::{Menu, MenuItem},
    tray::{TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_dialog::init())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // 系统托盘配置
      let quit_i = MenuItem::with_id(app, "quit", "退出 / Quit", true, None::<&str>)?;
      let show_i = MenuItem::with_id(app, "show", "显示主界面 / Show", true, None::<&str>)?;
      let menu = Menu::with_items(app, &[&show_i, &quit_i])?;

      let _tray = TrayIconBuilder::with_id("tray")
          .icon(app.default_window_icon().unwrap().clone())
          .menu(&menu)
          .on_menu_event(|app, event| match event.id.as_ref() {
              "quit" => {
                  app.exit(0);
              }
              "show" => {
                  if let Some(window) = app.get_webview_window("main") {
                      let _ = window.show();
                      let _ = window.set_focus();
                  }
              }
              _ => {}
          })
          .on_tray_icon_event(|tray, event| match event {
              TrayIconEvent::Click {
                  button: tauri::tray::MouseButton::Left,
                  ..
              } => {
                  let app = tray.app_handle();
                  if let Some(window) = app.get_webview_window("main") {
                      let _ = window.show();
                      let _ = window.set_focus();
                  }
              }
              _ => {}
          })
          .build(app)?;

      Ok(())
    })
    .on_window_event(|window, event| match event {
        WindowEvent::CloseRequested { api, .. } => {
            window.hide().unwrap();
            api.prevent_close();
        }
        _ => {}
    })
    .invoke_handler(tauri::generate_handler![open_external, select_folder])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

#[tauri::command]
fn open_external(url: String) -> Result<(), String> {
  #[cfg(not(target_os = "android"))]
  {
    use std::process::Command;
    let open_cmd = if cfg!(target_os = "windows") {
      "cmd"
    } else if cfg!(target_os = "macos") {
      "open"
    } else {
      "xdg-open"
    };
    
    let args: Vec<&str> = if cfg!(target_os = "windows") {
      vec!["/C", "start", "", url.as_str()]
    } else {
      vec![url.as_str()]
    };
    
    Command::new(open_cmd)
      .args(args)
      .spawn()
      .map_err(|e| format!("Failed to open URL: {}", e))?;
  }
  Ok(())
}

#[tauri::command]
fn select_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
  use tauri_plugin_dialog::DialogExt;
  use std::sync::mpsc;

  let (tx, rx) = mpsc::channel();

  app.dialog()
    .file()
    .set_title("选择工作区文件夹")
    .pick_folder(move |folder_path| {
      // FilePath 实现了 Display trait，可以直接 to_string()
      let result = folder_path.map(|p| p.to_string());
      let _ = tx.send(result);
    });

  // 阻塞当前线程等待回调结果（Tauri 默认在线程池运行命令，不会卡死 UI）
  rx.recv().map_err(|e| format!("Failed to receive folder path: {}", e))
}
