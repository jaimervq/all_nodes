use chrono::Local;

#[derive(Clone, Copy)]
pub enum Level {
    Info,
    Warn,
    Error,
    Debug,
}

fn level_str(level: Level) -> &'static str {
    match level {
        Level::Info => "INFO",
        Level::Warn => "WARNING",
        Level::Error => "ERROR",
        Level::Debug => "DEBUG",
    }
}

pub fn log(level: Level, msg: String, module: &str, file: &str, line: u32) {
    let name = level_str(level);

    println!(
        "{} {:>8}- 🦀 {} [{}] {}:{}",
        Local::now().format("%Y%m%d %H:%M:%S%.3f"),
        name,
        msg,
        module,
        file,
        line,
    );
}

// ----------------- MACROS ----------------- //
#[macro_export]
macro_rules! info {
    ($($arg:tt)*) => {
        $crate::log(
            $crate::Level::Info,
            format!($($arg)*),
            module_path!(),
            file!(),
            line!()
        )
    };
}

#[macro_export]
macro_rules! warning {
    ($($arg:tt)*) => {
        $crate::log(
            $crate::Level::Warn,
            format!($($arg)*),
            module_path!(),
            file!(),
            line!()
        )
    };
}

#[macro_export]
macro_rules! error {
    ($($arg:tt)*) => {
        $crate::log(
            $crate::Level::Error,
            format!($($arg)*),
            module_path!(),
            file!(),
            line!()
        )
    };
}

#[macro_export]
macro_rules! debug {
    ($($arg:tt)*) => {
        if cfg!(debug_assertions) {
            $crate::log(
                $crate::Level::Debug,
            format!($($arg)*),
            module_path!(),
            file!(),
            line!()
            )
        }
    };
}
