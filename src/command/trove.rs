use anyhow::{anyhow, Result};
use log::info;
use prettytable::{color, Attr, Cell, Row, Table};
use serde::{Deserialize, Serialize};

use std::collections::HashSet;
use std::{fs, path::Path, path::PathBuf};

use crate::command::HoardCommand;
use crate::command::parameters::Parameterized;
use crate::config::HoardConfig;
use crate::command::error::TroveError;

const CARGO_VERSION: &str = env!("CARGO_PKG_VERSION");

/// Container for all stored hoard commands.
/// A `treasure trove` of commands
///
/// A Trove can store the following parameters
/// - `version`: The hoard version with which the commands are being stored
///              To potentially support migrating older collections to new ones when breaking changes happen
/// - `commands`: Vector of `HoardCommand`s, the stored commands
/// - `namespaces`: Set of all namespaces used in the collection
#[derive(Debug, Serialize, Clone, Deserialize)]
pub struct Trove {
    pub version: String,
    pub commands: Vec<HoardCommand>,
    pub namespaces: HashSet<String>,
}

impl Default for Trove {
    /// Create a new trove collection with the currently running hoard version
    fn default() -> Self {
        Self {
            version: CARGO_VERSION.to_string(),
            commands: Vec::new(),
            namespaces: HashSet::new(),
        }
    }
}

impl Trove {
     /// Create a new Trove from a vector of commands
    /// attaches the current hoard version to the collection
    pub fn from_commands(commands: &[HoardCommand]) -> Self {
        // Iterate through all commands, read out the namespace and collect them in the namespace hashset
        let namespaces: HashSet<String> = commands
            .iter()
            .map(|c| c.namespace.clone())
            .collect::<HashSet<String>>();

        Self {
            version: CARGO_VERSION.to_string(),
            commands: commands.to_vec(),
            namespaces,
        }
    }

    /// Loads a local trove file and tries to parse it to load it into memory
    pub fn load_trove_file(path: &Option<PathBuf>) -> Self {
        path.clone().map_or_else(
            || {
                info!("[DEBUG] No trove path available. Creating new trove file");
                Self::default()
            },
            |p| {
                if p.exists() {
                    let f = std::fs::File::open(p).ok().unwrap();
                    let parsed_trove = serde_yaml::from_reader::<_, Self>(f);
                    match parsed_trove {
                        Ok(trove) => trove,
                        Err(e) => {
                            println!("The supplied trove file is invalid!");
                            println!("{e}");
                            Self::default()
                        }
                    }
                } else {
                    info!("[DEBUG] No trove file found at {:?}", p);
                    Self::default()
                }
            },
        )
    }

    /// Loads a trove collection from a string and tries to parse it to load it into memory
    pub fn load_trove_from_string(trove_string: &str) -> Self {
        let parsed_trove = serde_yaml::from_str::<Self>(trove_string);
        match parsed_trove {
            Ok(trove) => trove,
            Err(e) => {
                println!("{e}");
                println!("The supplied trove file is invalid!");
                Self::default()
            }
        }
    }

    /// Serialize trove collection to yaml format and returns it as a string
    pub fn to_yaml(&self) -> String {
        serde_yaml::to_string(&self).unwrap()
    }

    /// Save the trove collection to `path` as a yaml file
    pub fn save_trove_file(&self, path: &Path) {
        let s = self.to_yaml();
        fs::write(path, s).expect("Unable to write config file");
    }

    /// Given a `HoardCommand`, check if there is a command with the same name and namespace already in the collection
    /// If there is, return the colliding command
    /// If there is not, return `None`
    pub fn get_command_collision(&self, command: &HoardCommand) -> Option<HoardCommand> {
        let colliding_commands = self
            .commands
            .iter()
            .filter(|&c| c.namespace == command.namespace)
            .filter(|&c| c.name == command.name)
            .cloned();
        colliding_commands.into_iter().next()
    }

    /// Given a `HoardCommand`, check if there is a command with the same name, namespace and saved command already in the collection.
    /// A command with those same parameters is considered to be the same command
    /// If there is, return `true`
    /// If there is not, return `false`
    fn is_command_present(&self, command: &HoardCommand) -> bool {
        self.commands
            .iter()
            .filter(|&c| {
                c.namespace == command.namespace
                    && c.name == command.name
                    && c.command == command.command
            })
            .count()
            > 0
    }


    /// Add a command to trove file
    /// Returns `true` if the command has been added
    /// Returns `false` if the command has not been added due to a name collision that has been resolved where the trove did not change
    /// if `overwrite_colliding` is set to true, the name of the command will get a random string suffix to resolve the name collision before adding it to the trove
    /// if `overwrite_colliding` is set to false, the name collision will not be resolved and the command will not be added to the trove
    pub fn add_command(
        &mut self,
        new_command: HoardCommand,
        overwrite_colliding: bool,
    ) -> Result<bool, TroveError> {
        if !new_command.is_valid() {
            return Err(TroveError::new("cannot save invalid command"));
        }
        let dirty = match self.get_command_collision(&new_command) {
            // Collision is present, but its the same command, do nothing
            Some(_) if self.is_command_present(&new_command) => false,
            // collision is present, overwrite_colliding is true, resolve collision by overwriting
            Some(colliding_command) if overwrite_colliding => {
                self.commands.retain(|x| x != &colliding_command);
                self.commands.push(new_command);
                true
            }
            // collision is present, but overwrite_colliding is false, add random suffix before adding as a new comamnd
            Some(_) => {
                let c = new_command.with_random_name_suffix();
                self.commands.push(c);
                true
            }
            // If not collision, add the command
            None => {
                // no collision, maybe add the namespace
                self.add_namespace(&new_command.namespace);
                self.commands.push(new_command);
                true
            }
        };
        Ok(dirty)
    }

    /// try to add a namespace value to the namespaces if it is not present yet
    pub fn add_namespace(&mut self, namespace: &str) {
        if !self.namespaces.contains(namespace) {
            self.namespaces.insert(namespace.to_string());
        }
    }

    /// Remove a command from the trove collection
    /// Returns `Ok(())` if the command has been removed
    /// Returns `Err(anyhow::Error)` if the command to remove is not in the trove
    pub fn remove_command(&mut self, name: &str) -> Result<(), anyhow::Error> {
        let command_position = self.commands.iter().position(|x| x.name == name);
        if command_position.is_none() {
            return Err(anyhow!("Command not found [{}]", name));
        }
        self.commands.retain(|x| &*x.name != name);
        Ok(())
    }

    pub fn remove_namespace_commands(&mut self, namespace: &str) -> Result<(), anyhow::Error> {
        let command_position = self.commands.iter().position(|x| x.namespace == namespace);
        if command_position.is_none() {
            return Err(anyhow!("No Commands found in namespace [{}]", namespace));
        }
        self.commands.retain(|x| &*x.namespace != namespace);
        Ok(())
    }

    pub fn namespaces(&self) -> Vec<&str> {
        // Returns all namespaces in the trove
        let mut namespaces: Vec<_> = self
            .commands
            .iter()
            .map(|command| command.namespace.as_str())
            .collect::<HashSet<_>>()
            .into_iter()
            .collect();

        namespaces.sort_unstable();
        namespaces
    }

    pub fn pick_command(&self, config: &HoardConfig, name: &str) -> Result<HoardCommand> {
        let filtered_command: Option<&HoardCommand> = self.commands.iter().find(|c| c.name == name);
        filtered_command.map_or_else(
            || Err(anyhow!("No matching command found with name: {}", name)),
            |command| {
                let command = command
                    .clone()
                    .with_input_parameters(&config.parameter_token.clone().unwrap(), &config.parameter_ending_token.clone().unwrap());
                Ok(command)
            },
        )
    }

    pub fn update_command_by_name(&mut self, command: &HoardCommand) -> &mut Self {
        for c in &mut self.commands.iter_mut() {
            if c.name == command.name {
                *c = command.clone();
            }
        }
        self
    }

    /// check if the trove collection is empty
    pub fn is_empty(&self) -> bool {
        self.commands.is_empty()
    }

    pub fn merge_trove(&mut self, other: &Self) -> bool {
        other
            .commands
            .iter()
            .map(|c| self.add_command(c.clone(), true))
            .any(|x| x.is_ok())
    }

    pub fn print_trove(&self) {
        // Create the table
        let mut table = Table::new();
        // Add header
        table.add_row(row!["Name", "namespace", "command", "description", "tags"]);
        // Iterate through trove and populate table
        self.commands.iter().for_each(|c| {
            table.add_row(Row::new(vec![
                // Name
                Cell::new(&c.name[..])
                    .with_style(Attr::Bold)
                    .with_style(Attr::ForegroundColor(color::GREEN)),
                // namespace
                Cell::new(&c.namespace[..]),
                // command
                Cell::new(&c.command[..]),
                // description
                Cell::new(&c.description[..]),
                // tags
                Cell::new(&c.get_tags_as_string()),
            ]));
        });
        // Print the table to stdout
        table.printstd();
    }
}

#[cfg(test)]
mod test_commands {
    use super::*;

    #[test]
    fn empty_trove() {
        let trove = Trove::default();
        assert!(trove.is_empty());
    }

    #[test]
    fn not_empty_trove() {
        let mut trove = Trove::default();
        let command = HoardCommand::default().with_name("test").with_namespace("test-namespace").with_command("echo 'test'");
        let val = trove.add_command(command, true);
        assert!(val.is_ok());
        assert!(!trove.is_empty());
    }

    #[test]
    fn trove_namespaces() {
        let namespace1 = "NAMESPACE1";
        let namespace2 = "NAMESPACE2";

        let command1 = HoardCommand {
            name: "name1".to_string(),
            namespace: namespace1.to_string(),
            command: "command1".to_string(),
            ..HoardCommand::default()
        };

        let command2 = HoardCommand {
            name: "name2".to_string(),
            namespace: namespace2.to_string(),
            command: "command2".to_string(),
            ..HoardCommand::default()
        };

        let command3 = HoardCommand {
            name: "name3".to_string(),
            namespace: namespace1.to_string(),
            command: "command3".to_string(),
            ..HoardCommand::default()
        };

        let mut trove = Trove::default();
        let res1 = trove.add_command(command1, true);
        assert!(res1.is_ok());
        let res2 = trove.add_command(command2, true);
        assert!(res2.is_ok());
        let res3 = trove.add_command(command3, true);
        assert!(res3.is_ok());

        assert_eq!(vec![namespace1, namespace2], trove.namespaces());
    }
}
